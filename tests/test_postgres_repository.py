from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.repository import PostgresAnalysisRepository
from backend.app.service import AnalysisService
from backend.app.settings import Settings
from src.domain.models import (
    AnalysisResult,
    EmailMessage,
    HeaderData,
    PriorityLabel,
    PriorityResult,
    SecurityClassification,
    SecurityDecision,
    SecuritySignal,
    Sender,
    Severity,
)
from src.security.engine import SecurityEngine


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured; PostgreSQL integration requires a real PostgreSQL instance.",
)


class StubPhishing:
    def predict(self, text: str):
        return 0, -1.0


class StubPriority:
    def predict(self, text: str):
        return PriorityResult(PriorityLabel.P2)


def make_repo() -> PostgresAnalysisRepository:
    return PostgresAnalysisRepository(os.environ["TEST_DATABASE_URL"])


def make_service(repo: PostgresAnalysisRepository) -> AnalysisService:
    config = {
        "phishing": {
            "strong_score_threshold": 1.0,
            "suspicious_score_threshold": 0.0,
            "supporting_high_signals": 1,
        },
        "suspicious": {"minimum_meaningful_signals": 1},
        "require_phishing_model": True,
        "url": {"max_length": 2048, "max_count": 50, "max_subdomains": 4},
        "attachment": {"max_count": 25, "max_size_bytes": 10 * 1024 * 1024},
        "parser": {"max_bytes": 2_000_000},
    }
    return AnalysisService(SecurityEngine(config, StubPhishing(), StubPriority()), repo)


def make_client(repo: PostgresAnalysisRepository) -> TestClient:
    settings = Settings(
        environment="test",
        allowed_origins=("http://testserver",),
        database_url=os.environ["TEST_DATABASE_URL"],
        analysis_rate_limit=20,
        analysis_rate_window_seconds=60,
    )
    return TestClient(create_app(settings, make_service(repo)))


def make_email(message_id: str) -> EmailMessage:
    return EmailMessage(
        message_id=message_id,
        sender=Sender("sender@example.com", "Sender", "example.com"),
        recipients=("recipient@example.com", "audit@example.com"),
        subject="Quarterly report",
        text_body="Message body",
        headers=HeaderData({"x-test": "postgres"}),
        received_at=datetime(2026, 10, 7, 7, 0, tzinfo=timezone.utc),
    )


def make_result(message_id: str, request_id: str) -> AnalysisResult:
    reason = SecuritySignal(
        code="TEST_SIGNAL",
        severity=Severity.HIGH,
        category="TEST",
        message="Integration-test security finding.",
        evidence={"source": "postgres-integration"},
    )
    return AnalysisResult(
        message_id=message_id,
        security=SecurityDecision(
            SecurityClassification.SUSPICIOUS,
            (reason,),
            phishing_score=2.5,
            phishing_label=1,
        ),
        priority=PriorityResult(PriorityLabel.P2),
        request_id=request_id,
    )


def clear_tables(repo: PostgresAnalysisRepository) -> None:
    with repo._connect() as connection:
        connection.execute(
            "TRUNCATE analysis_results, sessions, workspace_members, workspaces, app_users RESTART IDENTITY CASCADE"
        )


@pytest.fixture()
def repo():
    repository = make_repo()
    clear_tables(repository)
    return repository


def test_postgres_schema_constraints_indexes_and_types(repo):
    with repo._connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()
        }
        assert {"app_users", "workspaces", "workspace_members", "sessions", "analysis_results"} <= tables

        columns = {
            row[0]: (row[1], row[2])
            for row in connection.execute(
                """
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='analysis_results'
                """
            ).fetchall()
        }
        assert columns["recipients_json"] == ("jsonb", "jsonb")
        assert columns["reasons_json"] == ("jsonb", "jsonb")
        assert columns["created_at"][0] == "timestamp with time zone"
        assert columns["received_at"][0] == "timestamp with time zone"

        constraints = [
            row[0].lower()
            for row in connection.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid IN ('sessions'::regclass, 'analysis_results'::regclass)
                """
            ).fetchall()
        ]
        assert any(
            "foreign key (workspace_id, user_id)" in definition
            and "references workspace_members(workspace_id, user_id)" in definition
            for definition in constraints
        )

        unique_indexes = [
            row[0].lower()
            for row in connection.execute(
                "SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='app_users'"
            ).fetchall()
        ]
        assert any("unique" in definition and "(email)" in definition for definition in unique_indexes)

        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename='analysis_results'"
            ).fetchall()
        }
        assert {
            "idx_analysis_workspace_created",
            "idx_analysis_workspace_classification",
            "idx_analysis_workspace_risk",
            "idx_analysis_workspace_message",
        } <= indexes


def test_postgres_authentication_sessions_and_expiry(repo):
    client = make_client(repo)
    email = f"{uuid4().hex}@example.com"
    password = "a-strong-test-password"

    register = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201, register.text
    cookie = register.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" not in cookie

    duplicate = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert duplicate.status_code == 409

    weak = client.post("/api/v1/auth/register", json={"email": f"{uuid4().hex}@example.com", "password": "weak"})
    assert weak.status_code == 422

    wrong = client.post("/api/v1/auth/login", json={"email": email, "password": "incorrect-password"})
    assert wrong.status_code == 401
    assert "incorrect-password" not in wrong.text
    assert password not in wrong.text

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200

    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    register_again = client.post(
        "/api/v1/auth/register",
        json={"email": f"{uuid4().hex}@example.com", "password": password},
    )
    assert register_again.status_code == 201

    with repo._connect() as connection:
        connection.execute(
            """
            UPDATE sessions
            SET expires_at=%s
            WHERE token_hash=(
                SELECT token_hash FROM sessions ORDER BY created_at DESC LIMIT 1
            )
            """,
            (datetime.now(timezone.utc) - timedelta(minutes=1),),
        )
    assert client.get("/api/v1/auth/me").status_code == 401


def test_postgres_persistence_contains_required_analysis_metadata(repo):
    user = repo.register_user(f"{uuid4().hex}@example.com", "password-hash")
    message_id = f"pg-{uuid4().hex}"
    request_id = f"req-{uuid4().hex}"
    repo.save(
        make_result(message_id, request_id),
        make_email(message_id),
        user_id=user["id"],
        workspace_id=user["workspace_id"],
        model_version="models-v1",
        policy_version="policy-v1",
    )

    row = repo.get(user["workspace_id"], message_id)
    assert row is not None
    assert row["message_id"] == message_id
    assert row["request_id"] == request_id
    assert row["sender"] == "sender@example.com"
    assert row["recipients"] == ["recipient@example.com", "audit@example.com"]
    assert row["subject"] == "Quarterly report"
    assert row["classification"] == "SUSPICIOUS"
    assert 0 <= float(row["risk_score"]) <= 100
    assert float(row["model_score"]) == 2.5
    assert row["reasons"][0]["code"] == "TEST_SIGNAL"
    assert row["priority"] == "P2"
    assert row["model_version"] == "models-v1"
    assert row["policy_version"] == "policy-v1"
    assert row["created_at"] is not None
    assert row["received_at"] is not None

    with repo._connect() as connection:
        stored_identity = connection.execute(
            "SELECT user_id, workspace_id FROM analysis_results WHERE message_id=%s",
            (message_id,),
        ).fetchone()
    assert tuple(stored_identity) == (user["id"], user["workspace_id"])


def test_postgres_workspace_isolation_covers_analysis_history_stats_and_reports(repo):
    client_a = make_client(repo)
    client_b = make_client(repo)
    password = "a-strong-test-password"
    email_a = f"{uuid4().hex}@example.com"
    email_b = f"{uuid4().hex}@example.com"

    a = client_a.post("/api/v1/auth/register", json={"email": email_a, "password": password})
    b = client_b.post("/api/v1/auth/register", json={"email": email_b, "password": password})
    assert a.status_code == 201 and b.status_code == 201

    body = {
        "message_id": f"iso-{uuid4().hex}",
        "sender": "sender@example.com",
        "recipients": ["recipient@example.com"],
        "subject": "Workspace A only",
        "text_body": "Normal message",
        "html_body": "",
        "headers": {},
        "attachments": [],
    }
    assert client_a.post("/api/v1/analyze", json=body).status_code == 200

    assert client_a.get("/api/v1/analysis/" + body["message_id"]).status_code == 200
    assert client_b.get("/api/v1/analysis/" + body["message_id"]).status_code == 404
    assert client_b.get("/api/v1/history").json()["total"] == 0
    assert client_b.get("/api/v1/stats").json()["total"] == 0
    assert client_b.get("/api/v1/reports/summary").json()["stats"]["total"] == 0
    assert client_b.get("/api/v1/reports/export?format=json").json()["items"] == []


def test_postgres_failed_transaction_rolls_back_all_statements(repo):
    email = f"{uuid4().hex}@example.com"

    with pytest.raises(psycopg.errors.UniqueViolation):
        with repo._connect() as connection:
            connection.execute(
                "INSERT INTO app_users(email,password_hash,created_at) VALUES(%s,%s,%s)",
                (email, "first", datetime.now(timezone.utc)),
            )
            connection.execute(
                "INSERT INTO app_users(email,password_hash,created_at) VALUES(%s,%s,%s)",
                (email, "second", datetime.now(timezone.utc)),
            )

    assert repo.get_user_by_email(email) is None
