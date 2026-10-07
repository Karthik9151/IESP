from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.repository import SQLiteAnalysisRepository
from backend.app.service import AnalysisService
from backend.app.settings import Settings
from src.domain.models import PriorityLabel, PriorityResult
from src.security.engine import SecurityEngine


class StubPhishing:
    def __init__(self, label: int = 0, score: float = -1.0):
        self.label = label
        self.score = score

    def predict(self, text: str):
        return self.label, self.score


class StubPriority:
    def predict(self, text: str):
        return PriorityResult(PriorityLabel.P2)


def make_file_client(tmp_path, label: int = 0, score: float = -1.0, rate_limit: int = 20):
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
    }
    engine = SecurityEngine(config, StubPhishing(label, score), StubPriority())
    repo = SQLiteAnalysisRepository(tmp_path / "api.sqlite3")
    service = AnalysisService(engine, repo)
    settings = Settings(
        environment="test",
        allowed_origins=("http://testserver",),
        database_path=tmp_path / "api.sqlite3",
        analysis_rate_limit=rate_limit,
        analysis_rate_window_seconds=60,
    )
    return TestClient(create_app(settings, service)), repo


BODY = {
    "message_id": "m1",
    "sender": "Sender <sender@example.com>",
    "recipients": ["user@example.com"],
    "subject": "Hello",
    "text_body": "team meeting tomorrow",
    "html_body": "",
    "headers": {},
    "attachments": [],
}


def register(client, email="user@example.com", password="a-strong-test-password"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    assert "Set-Cookie" in response.headers
    return response


def test_public_health_and_authentication(tmp_path):
    client, _ = make_file_client(tmp_path)
    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/analyze", json=BODY).status_code == 401

    register(client)
    assert client.get("/api/v1/auth/me").status_code == 200
    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_and_invalid_credentials(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    assert client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong-password"}).status_code == 401
    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "a-strong-test-password"})
    assert response.status_code == 200


def test_analysis_persists_real_email_metadata_and_contract(tmp_path):
    client, repo = make_file_client(tmp_path)
    register(client)
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-Request-ID": "req-123"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["request_id"] == "req-123"
    assert data["email"]["sender"] == "sender@example.com"
    assert data["email"]["subject"] == "Hello"
    assert data["security"]["classification"] == "NON-PHISHING"
    assert data["security"]["model_score_kind"] == "decision_margin"
    assert data["priority"]["label"] == "P2"
    assert data["security"]["risk_score"] == 10

    stored = repo.get(1, "m1")
    assert stored["sender"] == "sender@example.com"
    assert stored["subject"] == "Hello"
    assert stored["recipients"] == ["user@example.com"]
    assert stored["request_id"] == "req-123"
    assert stored["model_score"] == -1.0


def test_phishing_and_review_suppress_priority(tmp_path):
    client, _ = make_file_client(tmp_path, label=1, score=2.0)
    register(client)
    response = client.post("/api/v1/analyze", json={**BODY, "headers": {"authentication-results": "spf=fail"}})
    assert response.status_code == 200
    data = response.json()
    assert data["security"]["classification"] == "PHISHING"
    assert data["priority"] is None


def test_validation_and_request_id_header(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    invalid = client.post("/api/v1/analyze", json={**BODY, "unexpected": "x"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert invalid.json()["error"]["request_id"]

    response = client.post("/api/v1/analyze", json=BODY, headers={"X-Request-ID": "req.safe-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req.safe-123"


def test_oversized_request_and_email_are_rejected(tmp_path):
    big_root = tmp_path / "small"
    client, _ = make_file_client(big_root)
    register(client)
    settings = Settings(
        environment="test",
        allowed_origins=("http://testserver",),
        database_path=tmp_path / "small.sqlite3",
        max_request_bytes=256,
        max_email_bytes=128,
    )
    service = AnalysisService(
        SecurityEngine({"require_phishing_model": False}),
        SQLiteAnalysisRepository(tmp_path / "small.sqlite3"),
    )
    small = TestClient(create_app(settings, service))
    register(small, "small@example.com")
    response = small.post("/api/v1/analyze", json={**BODY, "text_body": "x" * 400})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_eml_workflow_and_safe_error(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    raw = (
        b"From: Sender <sender@example.com>\r\n"
        b"To: user@example.com\r\n"
        b"Subject: Test\r\n"
        b"Message-ID: <m-eml@example.com>\r\n"
        b"\r\nHello\r\n"
    )
    response = client.post("/api/v1/analyze/eml", files={"file": ("mail.eml", raw, "message/rfc822")})
    assert response.status_code == 200, response.text
    assert response.json()["email"]["message_id"] == "m-eml@example.com"

    wrong = client.post("/api/v1/analyze/eml", files={"file": ("mail.txt", raw, "text/plain")})
    assert wrong.status_code == 422
    assert wrong.json()["error"]["code"] == "UNSUPPORTED_FILE"


def test_workspace_isolation(tmp_path):
    client_a, _ = make_file_client(tmp_path / "a")
    client_b, _ = make_file_client(tmp_path / "b")
    register(client_a, "a@example.com")
    register(client_b, "b@example.com")
    client_a.post("/api/v1/analyze", json=BODY)
    response = client_b.get("/api/v1/analysis/m1")
    assert response.status_code == 404


def test_history_filters_pagination_and_reports(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    for number in range(3):
        body = {**BODY, "message_id": f"m{number}", "sender": f"s{number}@example.com", "subject": f"Subject {number}"}
        assert client.post("/api/v1/analyze", json=body).status_code == 200
    history = client.get("/api/v1/history?page=1&page_size=2&q=s1")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["sender"] == "s1@example.com"

    stats = client.get("/api/v1/stats")
    assert stats.status_code == 200
    assert stats.json()["total"] == 3

    report = client.get("/api/v1/reports/summary")
    assert report.status_code == 200

    export = client.get("/api/v1/reports/export?format=csv")
    assert export.status_code == 200
    assert "message_id" in export.text.splitlines()[0]


def test_rate_limit_returns_retry_after(tmp_path):
    client, _ = make_file_client(tmp_path, rate_limit=1)
    register(client)
    assert client.post("/api/v1/analyze", json=BODY).status_code == 200
    second = client.post("/api/v1/analyze", json={**BODY, "message_id": "m2"})
    assert second.status_code == 429
    assert second.headers.get("Retry-After")
    assert second.json()["error"]["code"] == "RATE_LIMITED"


def test_expired_session_is_invalid(tmp_path):
    client, repo = make_file_client(tmp_path)
    register(client)
    with repo._connect() as connection:
        connection.execute(
            "UPDATE sessions SET expires_at=?",
            ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),),
        )
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_INVALID"


def test_eml_multipart_attachment_and_suspicious_url_workflow(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    boundary = "iesp-boundary"
    raw = (
        f"From: Sender <sender@example.com>\r\n"
        f"To: user@example.com\r\n"
        f"Subject: Multipart security test\r\n"
        f"Message-ID: <m-multipart@example.com>\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/alternative; boundary=\"{boundary}\"\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"Visit http://127.0.0.1:8080/admin\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n\r\n"
        f"<html><body><a href=\"http://127.0.0.1:8080/admin\">Review</a></body></html>\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: application/pdf\r\n"
        f"Content-Disposition: attachment; filename=\"../../invoice.pdf.exe\"\r\n\r\n"
        f"not-executed-payload\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    response = client.post(
        "/api/v1/analyze/eml",
        files={"file": ("multipart.eml", raw, "message/rfc822")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"]["message_id"] == "m-multipart@example.com"
    reason_codes = {reason["code"] for reason in data["security"]["reasons"]}
    assert "SSRF_SENSITIVE_DESTINATION" in reason_codes
    assert "DANGEROUS_EXTENSION" in reason_codes
    assert "DOUBLE_EXTENSION" in reason_codes


def test_eml_malformed_headers_and_mime_fail_closed(tmp_path):
    client, _ = make_file_client(tmp_path)
    register(client)
    malformed = (
        b"From: Sender <sender@example.com>\r\n"
        b"To: user@example.com\r\n"
        b"Bad Header Name: value\r\n"
        b"\r\n"
        b"body\r\n"
    )
    response = client.post(
        "/api/v1/analyze/eml",
        files={"file": ("malformed.eml", malformed, "message/rfc822")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMAIL_PARSE_ERROR"
