from __future__ import annotations

from src.domain.models import AnalysisResult, EmailMessage, HeaderData, SecurityClassification, SecurityDecision, Sender
from backend.app.repository import SQLiteAnalysisRepository


def make_email(message_id: str, sender: str, subject: str, recipient: str) -> EmailMessage:
    return EmailMessage(
        message_id=message_id,
        sender=Sender(sender, domain=sender.rsplit("@", 1)[1]),
        recipients=(recipient,),
        subject=subject,
        text_body="message body",
        headers=HeaderData({}),
    )


def test_sqlite_repository_persists_analysis_metadata_and_workspace_scope(tmp_path):
    repo = SQLiteAnalysisRepository(tmp_path / "analysis.sqlite3")
    result = AnalysisResult(
        "m-1",
        SecurityDecision(SecurityClassification.SUSPICIOUS, ()),
        None,
        "req-1",
    )
    email = make_email("m-1", "sender@example.com", "Quarterly report", "user@example.com")
    repo.register_user("user@example.com", "hash")
    repo.save(result, email, user_id=1, workspace_id=1, model_version="models-v1", policy_version="policy-v1")

    stored = repo.get(1, "m-1")
    assert stored is not None
    assert stored["message_id"] == "m-1"
    assert stored["sender"] == "sender@example.com"
    assert stored["recipients"] == ["user@example.com"]
    assert stored["subject"] == "Quarterly report"
    assert stored["classification"] == "SUSPICIOUS"
    assert stored["request_id"] == "req-1"
    assert stored["model_version"] == "models-v1"
    assert stored["policy_version"] == "policy-v1"
    assert repo.get(999, "m-1") is None

    stats = repo.stats(1)
    assert stats["total"] == 1
    assert stats["suspicious"] == 1
    assert stats["high_risk"] == 0


def test_history_filters_and_pagination_are_workspace_scoped(tmp_path):
    repo = SQLiteAnalysisRepository(tmp_path / "history.sqlite3")
    repo.register_user("one@example.com", "hash")
    repo.register_user("two@example.com", "hash")
    for user_id, workspace_id, number in [(1, 1, 1), (1, 1, 2), (2, 2, 3)]:
        message_id = f"m-{number}"
        result = AnalysisResult(message_id, SecurityDecision(SecurityClassification.NON_PHISHING, ()), None, f"r-{number}")
        email = make_email(message_id, f"sender{number}@example.com", f"Subject {number}", f"u{number}@example.com")
        repo.save(result, email, user_id, workspace_id, "models-v1", "policy-v1")

    page = repo.history(1, page=1, page_size=1, search="Subject 2")
    assert page["total"] == 1
    assert page["items"][0]["message_id"] == "m-2"
    assert repo.history(1, search="Subject 3")["total"] == 0
