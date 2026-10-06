from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from src.domain.models import AnalysisResult


class AnalysisRepository(Protocol):
    def save(self, result: AnalysisResult) -> None: ...
    def get(self, message_id: str) -> dict | None: ...
    def recent(self, limit: int = 50) -> list[dict]: ...
    def stats(self) -> dict[str, int]: ...


class SQLiteAnalysisRepository:
    """Small SQLite persistence boundary that stores analysis metadata only."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    reasons_json TEXT NOT NULL,
                    priority_label TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_message_id ON analysis_results(message_id)")

    def save(self, result: AnalysisResult) -> None:
        reasons = [{"code": r.code, "severity": r.severity.value, "category": r.category, "message": r.message, "evidence": r.evidence} for r in result.security.reasons]
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO analysis_results (message_id, request_id, classification, reasons_json, priority_label, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (result.message_id, result.request_id or "", result.security.classification.value, json.dumps(reasons, sort_keys=True, ensure_ascii=False), result.priority.label.value if result.priority else None, datetime.now(timezone.utc).isoformat()),
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        return {"message_id": row["message_id"], "request_id": row["request_id"], "classification": row["classification"], "reasons": json.loads(row["reasons_json"]), "priority": row["priority_label"], "created_at": row["created_at"]}

    def get(self, message_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT message_id, request_id, classification, reasons_json, priority_label, created_at FROM analysis_results WHERE message_id = ? ORDER BY id DESC LIMIT 1", (message_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def recent(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with self._connect() as conn:
            rows = conn.execute("SELECT message_id, request_id, classification, reasons_json, priority_label, created_at FROM analysis_results ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM analysis_results").fetchone()[0]
            rows = conn.execute("SELECT classification, COUNT(*) AS count FROM analysis_results GROUP BY classification").fetchall()
        counts = {row["classification"]: int(row["count"]) for row in rows}
        return {"total": int(total), "phishing": counts.get("PHISHING", 0), "suspicious": counts.get("SUSPICIOUS", 0), "non_phishing": counts.get("NON-PHISHING", 0), "review_required": counts.get("REVIEW REQUIRED", 0)}
