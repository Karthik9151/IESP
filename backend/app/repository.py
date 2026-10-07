from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.domain.models import AnalysisResult, EmailMessage

from .risk import policy_risk_score


class AnalysisRepository(Protocol):
    def save(self, result: AnalysisResult, email: EmailMessage, user_id: int, workspace_id: int, model_version: str, policy_version: str) -> None: ...
    def get(self, workspace_id: int, message_id: str) -> dict[str, Any] | None: ...
    def history(self, workspace_id: int, **filters: Any) -> dict[str, Any]: ...
    def stats(self, workspace_id: int, high_risk_threshold: float = 75.0) -> dict[str, Any]: ...
    def register_user(self, email: str, password_hash: str) -> dict[str, Any]: ...
    def get_user_by_email(self, email: str) -> dict[str, Any] | None: ...
    def get_user(self, user_id: int, workspace_id: int) -> dict[str, Any] | None: ...
    def create_session(self, token_hash: str, user_id: int, workspace_id: int, expires_at: datetime) -> None: ...
    def get_session(self, token_hash: str) -> dict[str, Any] | None: ...
    def delete_session(self, token_hash: str) -> None: ...
    def ping(self) -> bool: ...


SQLITE_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS app_users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspaces(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspace_members(
    workspace_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY(workspace_id,user_id),
    FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sessions(
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    workspace_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE,
    FOREIGN KEY(workspace_id,user_id) REFERENCES workspace_members(workspace_id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS analysis_results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    workspace_id INTEGER NOT NULL,
    sender_email TEXT NOT NULL,
    recipients_json TEXT NOT NULL DEFAULT '[]',
    subject TEXT NOT NULL,
    classification TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    priority_label TEXT,
    risk_score REAL NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100),
    model_score REAL,
    created_at TEXT NOT NULL,
    received_at TEXT,
    model_version TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE,
    FOREIGN KEY(workspace_id,user_id) REFERENCES workspace_members(workspace_id,user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_created ON analysis_results(workspace_id,created_at DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_classification ON analysis_results(workspace_id,classification);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_risk ON analysis_results(workspace_id,risk_score);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_message ON analysis_results(workspace_id,message_id,id DESC);
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_users(
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS workspaces(
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS workspace_members(
    workspace_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY(workspace_id,user_id),
    FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sessions(
    token_hash TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    workspace_id BIGINT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE,
    FOREIGN KEY(workspace_id,user_id) REFERENCES workspace_members(workspace_id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS analysis_results(
    id BIGSERIAL PRIMARY KEY,
    message_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    workspace_id BIGINT NOT NULL,
    sender_email TEXT NOT NULL,
    recipients_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    subject TEXT NOT NULL,
    classification TEXT NOT NULL,
    reasons_json JSONB NOT NULL,
    priority_label TEXT,
    risk_score DOUBLE PRECISION NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100),
    model_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ,
    model_version TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE,
    FOREIGN KEY(workspace_id,user_id) REFERENCES workspace_members(workspace_id,user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_created ON analysis_results(workspace_id,created_at DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_classification ON analysis_results(workspace_id,classification);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_risk ON analysis_results(workspace_id,risk_score);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_message ON analysis_results(workspace_id,message_id,id DESC);
"""

_ALLOWED_SORT = {
    "created_at": "created_at",
    "risk_score": "risk_score",
    "classification": "classification",
    "sender": "sender_email",
    "subject": "subject",
}


def _iso(value: datetime | str | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def _serialize_result(result: AnalysisResult, email: EmailMessage, model_version: str, policy_version: str) -> tuple[Any, ...]:
    reasons = [
        {"code": item.code, "severity": item.severity.value, "category": item.category, "message": item.message, "evidence": item.evidence}
        for item in result.security.reasons
    ]
    return (
        result.message_id,
        result.request_id or "",
        email.sender.address,
        json.dumps(list(email.recipients), sort_keys=True),
        email.subject,
        result.security.classification.value,
        json.dumps(reasons, sort_keys=True),
        result.priority.label.value if result.priority else None,
        policy_risk_score(result.security.classification.value, reasons),
        result.security.phishing_score,
        _iso(email.received_at),
        model_version,
        policy_version,
    )


class SQLiteAnalysisRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(SQLITE_SCHEMA)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(analysis_results)")}
            migrations = {
                "recipients_json": "TEXT NOT NULL DEFAULT '[]'",
                "model_score": "REAL",
                "received_at": "TEXT",
                "model_version": "TEXT NOT NULL DEFAULT 'legacy'",
                "policy_version": "TEXT NOT NULL DEFAULT 'legacy'",
            }
            for name, definition in migrations.items():
                if name not in columns:
                    connection.execute(f"ALTER TABLE analysis_results ADD COLUMN {name} {definition}")

    def ping(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    def register_user(self, email: str, password_hash: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as connection:
                if connection.execute("SELECT 1 FROM app_users WHERE email=?", (email,)).fetchone():
                    raise ValueError("EMAIL_EXISTS")
                user_id = int(connection.execute(
                    "INSERT INTO app_users(email,password_hash,created_at) VALUES(?,?,?) RETURNING id",
                    (email, password_hash, now),
                ).fetchone()[0])
                workspace_name = f"{email} workspace"
                workspace_id = int(connection.execute(
                    "INSERT INTO workspaces(name,created_at) VALUES(?,?) RETURNING id",
                    (workspace_name, now),
                ).fetchone()[0])
                connection.execute(
                    "INSERT INTO workspace_members(workspace_id,user_id,role) VALUES(?,?,?)",
                    (workspace_id, user_id, "owner"),
                )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("EMAIL_EXISTS") from exc
            raise
        return {"id": user_id, "email": email, "workspace_id": workspace_id, "workspace_name": workspace_name, "role": "owner"}

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT u.id,u.email,u.password_hash,w.id workspace_id,w.name workspace_name,wm.role
                   FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id
                   JOIN workspaces w ON w.id=wm.workspace_id WHERE u.email=? ORDER BY w.id LIMIT 1""",
                (email,),
            ).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: int, workspace_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT u.id,u.email,w.id workspace_id,w.name workspace_name,wm.role
                   FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id
                   JOIN workspaces w ON w.id=wm.workspace_id WHERE u.id=? AND w.id=?""",
                (user_id, workspace_id),
            ).fetchone()
        return dict(row) if row else None

    def create_session(self, token_hash: str, user_id: int, workspace_id: int, expires_at: datetime) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions(token_hash,user_id,workspace_id,expires_at,created_at) VALUES(?,?,?,?,?)",
                (token_hash, user_id, workspace_id, expires_at.isoformat(), datetime.now(timezone.utc).isoformat()),
            )

    def get_session(self, token_hash: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT s.user_id,s.workspace_id,s.expires_at,u.email,wm.role
                   FROM sessions s JOIN app_users u ON u.id=s.user_id
                   JOIN workspace_members wm ON wm.workspace_id=s.workspace_id AND wm.user_id=s.user_id
                   WHERE s.token_hash=?""",
                (token_hash,),
            ).fetchone()
        if not row:
            return None
        if datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
            self.delete_session(token_hash)
            return None
        return dict(row)

    def delete_session(self, token_hash: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))

    def save(self, result: AnalysisResult, email: EmailMessage, user_id: int, workspace_id: int, model_version: str = "models-v1", policy_version: str = "policy-v1") -> None:
        values = _serialize_result(result, email, model_version, policy_version)
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO analysis_results(
                       message_id,request_id,sender_email,recipients_json,subject,classification,reasons_json,
                       priority_label,risk_score,model_score,received_at,model_version,policy_version,user_id,workspace_id,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*values, user_id, workspace_id, datetime.now(timezone.utc).isoformat()),
            )

    def _where(self, workspace_id: int, search=None, classification=None, min_risk=None, max_risk=None, date_from=None, date_to=None):
        clauses, params = ["workspace_id=?"], [workspace_id]
        if search:
            term = f"%{search.lower()}%"
            clauses.append("(LOWER(sender_email) LIKE ? OR LOWER(subject) LIKE ?)")
            params.extend([term, term])
        if classification:
            clauses.append("classification=?")
            params.append(classification)
        if min_risk is not None:
            clauses.append("risk_score>=?")
            params.append(min_risk)
        if max_risk is not None:
            clauses.append("risk_score<=?")
            params.append(max_risk)
        if date_from:
            clauses.append("created_at>=?")
            params.append(_iso(date_from))
        if date_to:
            clauses.append("created_at<=?")
            params.append(_iso(date_to))
        return " AND ".join(clauses), params

    def get(self, workspace_id: int, message_id: str):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM analysis_results WHERE workspace_id=? AND message_id=? ORDER BY id DESC LIMIT 1",
                (workspace_id, message_id),
            ).fetchone()
        return self._row(row) if row else None

    def history(self, workspace_id: int, *, page=1, page_size=25, search=None, classification=None, min_risk=None, max_risk=None, date_from=None, date_to=None, sort_by="created_at", sort_order="desc"):
        page, page_size = max(1, int(page)), max(1, min(int(page_size), 100))
        sort_column = _ALLOWED_SORT.get(sort_by, "created_at")
        direction = "ASC" if str(sort_order).lower() == "asc" else "DESC"
        where, params = self._where(workspace_id, search, classification, min_risk, max_risk, date_from, date_to)
        offset = (page - 1) * page_size
        with self._connect() as connection:
            total = int(connection.execute(f"SELECT COUNT(*) FROM analysis_results WHERE {where}", params).fetchone()[0])
            rows = connection.execute(
                f"SELECT * FROM analysis_results WHERE {where} ORDER BY {sort_column} {direction}, id DESC LIMIT ? OFFSET ?",
                (*params, page_size, offset),
            ).fetchall()
        return {"items": [self._row(row) for row in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def stats(self, workspace_id: int, high_risk_threshold: float = 75.0):
        with self._connect() as connection:
            total = int(connection.execute("SELECT COUNT(*) FROM analysis_results WHERE workspace_id=?", (workspace_id,)).fetchone()[0])
            rows = connection.execute(
                "SELECT classification,COUNT(*) count FROM analysis_results WHERE workspace_id=? GROUP BY classification",
                (workspace_id,),
            ).fetchall()
            high_risk = int(connection.execute(
                "SELECT COUNT(*) FROM analysis_results WHERE workspace_id=? AND risk_score>=?",
                (workspace_id, high_risk_threshold),
            ).fetchone()[0])
        counts = {row["classification"]: int(row["count"]) for row in rows}
        return {
            "total": total,
            "phishing": counts.get("PHISHING", 0),
            "suspicious": counts.get("SUSPICIOUS", 0),
            "non_phishing": counts.get("NON-PHISHING", 0),
            "review_required": counts.get("REVIEW REQUIRED", 0),
            "high_risk": high_risk,
            "high_risk_percentage": round((high_risk / total) * 100, 1) if total else 0.0,
        }

    @staticmethod
    def _row(row):
        return {
            "message_id": row["message_id"],
            "request_id": row["request_id"],
            "sender": row["sender_email"],
            "recipients": json.loads(row["recipients_json"] or "[]"),
            "subject": row["subject"],
            "classification": row["classification"],
            "reasons": json.loads(row["reasons_json"] or "[]"),
            "priority": row["priority_label"],
            "risk_score": row["risk_score"],
            "model_score": row["model_score"],
            "created_at": row["created_at"],
            "received_at": row["received_at"],
            "model_version": row["model_version"],
            "policy_version": row["policy_version"],
        }


class PostgresAnalysisRepository:
    def __init__(self, url: str) -> None:
        import psycopg
        self.psycopg = psycopg
        self.url = url.replace("postgres://", "postgresql://", 1)
        self._init_db()

    def _connect(self):
        return self.psycopg.connect(self.url)

    def _init_db(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for statement in (item.strip() for item in PG_SCHEMA.split(";") if item.strip()):
                    cursor.execute(statement)
                cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS recipients_json JSONB NOT NULL DEFAULT '[]'::jsonb")
                cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS model_score DOUBLE PRECISION")
                cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ")
                cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS model_version TEXT NOT NULL DEFAULT 'legacy'")
                cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS policy_version TEXT NOT NULL DEFAULT 'legacy'")

    def ping(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    def register_user(self, email: str, password_hash: str):
        now = datetime.now(timezone.utc)
        try:
            with self._connect() as connection:
                if connection.execute("SELECT 1 FROM app_users WHERE email=%s", (email,)).fetchone():
                    raise ValueError("EMAIL_EXISTS")
                user_id = connection.execute(
                    "INSERT INTO app_users(email,password_hash,created_at) VALUES(%s,%s,%s) RETURNING id",
                    (email, password_hash, now),
                ).fetchone()[0]
                workspace_name = f"{email} workspace"
                workspace_id = connection.execute(
                    "INSERT INTO workspaces(name,created_at) VALUES(%s,%s) RETURNING id",
                    (workspace_name, now),
                ).fetchone()[0]
                connection.execute(
                    "INSERT INTO workspace_members(workspace_id,user_id,role) VALUES(%s,%s,%s)",
                    (workspace_id, user_id, "owner"),
                )
        except self.psycopg.errors.UniqueViolation as exc:
            raise ValueError("EMAIL_EXISTS") from exc
        return {"id": int(user_id), "email": email, "workspace_id": int(workspace_id), "workspace_name": workspace_name, "role": "owner"}

    def get_user_by_email(self, email: str):
        with self._connect() as connection:
            row = connection.execute(
                """SELECT u.id,u.email,u.password_hash,w.id workspace_id,w.name workspace_name,wm.role
                   FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id
                   JOIN workspaces w ON w.id=wm.workspace_id WHERE u.email=%s ORDER BY w.id LIMIT 1""",
                (email,),
            ).fetchone()
        if not row:
            return None
        return {"id": int(row[0]), "email": row[1], "password_hash": row[2], "workspace_id": int(row[3]), "workspace_name": row[4], "role": row[5]}

    def get_user(self, user_id: int, workspace_id: int):
        with self._connect() as connection:
            row = connection.execute(
                """SELECT u.id,u.email,w.id workspace_id,w.name workspace_name,wm.role
                   FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id
                   JOIN workspaces w ON w.id=wm.workspace_id WHERE u.id=%s AND w.id=%s""",
                (user_id, workspace_id),
            ).fetchone()
        if not row:
            return None
        return {"id": int(row[0]), "email": row[1], "workspace_id": int(row[2]), "workspace_name": row[3], "role": row[4]}

    def create_session(self, token_hash: str, user_id: int, workspace_id: int, expires_at: datetime) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions(token_hash,user_id,workspace_id,expires_at,created_at) VALUES(%s,%s,%s,%s,%s)",
                (token_hash, user_id, workspace_id, expires_at, datetime.now(timezone.utc)),
            )

    def get_session(self, token_hash: str):
        with self._connect() as connection:
            row = connection.execute(
                """SELECT s.user_id,s.workspace_id,s.expires_at,u.email,wm.role
                   FROM sessions s JOIN app_users u ON u.id=s.user_id
                   JOIN workspace_members wm ON wm.workspace_id=s.workspace_id AND wm.user_id=s.user_id
                   WHERE s.token_hash=%s""",
                (token_hash,),
            ).fetchone()
        if not row:
            return None
        expires_at = row[2]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            self.delete_session(token_hash)
            return None
        return {"user_id": int(row[0]), "workspace_id": int(row[1]), "expires_at": row[2], "email": row[3], "role": row[4]}

    def delete_session(self, token_hash: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash=%s", (token_hash,))

    def save(self, result: AnalysisResult, email: EmailMessage, user_id: int, workspace_id: int, model_version: str = "models-v1", policy_version: str = "policy-v1") -> None:
        reasons = [
            {"code": item.code, "severity": item.severity.value, "category": item.category, "message": item.message, "evidence": item.evidence}
            for item in result.security.reasons
        ]
        values = (
            result.message_id,
            result.request_id or "",
            user_id,
            workspace_id,
            email.sender.address,
            json.dumps(list(email.recipients)),
            email.subject,
            result.security.classification.value,
            json.dumps(reasons, sort_keys=True),
            result.priority.label.value if result.priority else None,
            policy_risk_score(result.security.classification.value, reasons),
            result.security.phishing_score,
            datetime.now(timezone.utc),
            email.received_at,
            model_version,
            policy_version,
        )
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO analysis_results(
                    message_id,request_id,user_id,workspace_id,sender_email,recipients_json,subject,classification,
                    reasons_json,priority_label,risk_score,model_score,created_at,received_at,model_version,policy_version
                ) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)""",
                values,
            )

    def _where(self, workspace_id: int, search=None, classification=None, min_risk=None, max_risk=None, date_from=None, date_to=None):
        clauses, params = ["workspace_id=%s"], [workspace_id]
        if search:
            term = f"%{search.lower()}%"
            clauses.append("(LOWER(sender_email) LIKE %s OR LOWER(subject) LIKE %s)")
            params.extend([term, term])
        if classification:
            clauses.append("classification=%s")
            params.append(classification)
        if min_risk is not None:
            clauses.append("risk_score>=%s")
            params.append(min_risk)
        if max_risk is not None:
            clauses.append("risk_score<=%s")
            params.append(max_risk)
        if date_from:
            clauses.append("created_at>=%s")
            params.append(date_from)
        if date_to:
            clauses.append("created_at<=%s")
            params.append(date_to)
        return " AND ".join(clauses), params

    def get(self, workspace_id: int, message_id: str):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM analysis_results WHERE workspace_id=%s AND message_id=%s ORDER BY id DESC LIMIT 1",
                (workspace_id, message_id),
            ).fetchone()
        return self._row(row) if row else None

    def history(self, workspace_id: int, *, page=1, page_size=25, search=None, classification=None, min_risk=None, max_risk=None, date_from=None, date_to=None, sort_by="created_at", sort_order="desc"):
        page, page_size = max(1, int(page)), max(1, min(int(page_size), 100))
        sort_column = _ALLOWED_SORT.get(sort_by, "created_at")
        direction = "ASC" if str(sort_order).lower() == "asc" else "DESC"
        where, params = self._where(workspace_id, search, classification, min_risk, max_risk, date_from, date_to)
        offset = (page - 1) * page_size
        with self._connect() as connection:
            total = int(connection.execute(f"SELECT COUNT(*) FROM analysis_results WHERE {where}", params).fetchone()[0])
            rows = connection.execute(
                f"SELECT * FROM analysis_results WHERE {where} ORDER BY {sort_column} {direction}, id DESC LIMIT %s OFFSET %s",
                (*params, page_size, offset),
            ).fetchall()
        return {"items": [self._row(row) for row in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

    def stats(self, workspace_id: int, high_risk_threshold: float = 75.0):
        with self._connect() as connection:
            total = int(connection.execute("SELECT COUNT(*) FROM analysis_results WHERE workspace_id=%s", (workspace_id,)).fetchone()[0])
            rows = connection.execute(
                "SELECT classification,COUNT(*) FROM analysis_results WHERE workspace_id=%s GROUP BY classification",
                (workspace_id,),
            ).fetchall()
            high_risk = int(connection.execute(
                "SELECT COUNT(*) FROM analysis_results WHERE workspace_id=%s AND risk_score>=%s",
                (workspace_id, high_risk_threshold),
            ).fetchone()[0])
        counts = {row[0]: int(row[1]) for row in rows}
        return {
            "total": total,
            "phishing": counts.get("PHISHING", 0),
            "suspicious": counts.get("SUSPICIOUS", 0),
            "non_phishing": counts.get("NON-PHISHING", 0),
            "review_required": counts.get("REVIEW REQUIRED", 0),
            "high_risk": high_risk,
            "high_risk_percentage": round((high_risk / total) * 100, 1) if total else 0.0,
        }

    @staticmethod
    def _row(row):
        return {
            "message_id": row[1],
            "request_id": row[2],
            "sender": row[5],
            "recipients": list(row[6] or []),
            "subject": row[7],
            "classification": row[8],
            "reasons": list(row[9] or []),
            "priority": row[10],
            "risk_score": row[11],
            "model_score": row[12],
            "created_at": row[13],
            "received_at": row[14],
            "model_version": row[15],
            "policy_version": row[16],
        }


def build_repository(settings) -> AnalysisRepository:
    if settings.database_url.startswith(("postgres://", "postgresql://")):
        return PostgresAnalysisRepository(settings.database_url)
    return SQLiteAnalysisRepository(settings.database_path)
