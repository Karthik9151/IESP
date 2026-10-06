from __future__ import annotations

from src.domain.models import AnalysisResult, SecurityClassification, SecurityDecision
from backend.app.repository import SQLiteAnalysisRepository


def test_sqlite_repository_persists_only_analysis_metadata(tmp_path):
    repo = SQLiteAnalysisRepository(tmp_path / "analysis.sqlite3")
    result = AnalysisResult("m-1", SecurityDecision(SecurityClassification.SUSPICIOUS, ()), None, "req-1")
    repo.save(result)
    stored = repo.get("m-1")
    assert stored["message_id"] == "m-1"
    assert stored["classification"] == "SUSPICIOUS"
    assert stored["priority"] is None
    stats = repo.stats()
    assert stats["total"] == 1
    assert stats["suspicious"] == 1
