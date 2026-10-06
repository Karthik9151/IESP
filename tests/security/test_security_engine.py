from src.domain.models import (
    AttachmentMetadata, EmailMessage, HeaderData, SecurityClassification,
    Sender, UrlMetadata
)
from src.parsing.email_parser import EmailParseError, parse_email_text
from src.security.analysis import analyze_email_security
from src.security.decision import decide_security
from src.security.logging_policy import sanitize_log_fields

CONFIG = {
    "phishing": {"strong_score_threshold": 1.0, "suspicious_score_threshold": 0.0, "supporting_high_signals": 1},
    "suspicious": {"minimum_meaningful_signals": 1},
    "require_phishing_model": True,
    "url": {"max_length": 2048, "max_count": 50, "max_subdomains": 4},
    "attachment": {"max_count": 25, "max_size_bytes": 100},
}


def make_email(**kwargs):
    return EmailMessage(
        message_id="m1",
        sender=Sender("attacker@example.com", domain="attacker.com"),
        recipients=("user@example.com",),
        headers=HeaderData(kwargs.pop("headers", {})),
        attachments=kwargs.pop("attachments", ()),
        urls=kwargs.pop("urls", ()),
        subject=kwargs.pop("subject", ""),
        text_body=kwargs.pop("text_body", ""),
    )


def test_malformed_mime_is_rejected():
    raw = 'From: sender@example.com\nTo: receiver@example.com\nSubject: test\nContent-Type: multipart/mixed; boundary="x"\n\n--x\n'
    with __import__("pytest").raises(EmailParseError):
        parse_email_text(raw)


def test_header_mismatch_and_auth_failure():
    email = make_email(headers={"reply-to": "support@different.com", "authentication-results": "spf=fail dkim=fail"})
    codes = {s.code for s in analyze_email_security(email, CONFIG).signals}
    assert {"FROM_REPLY_TO_MISMATCH", "AUTHENTICATION_FAILURE"} <= codes


def test_url_structural_ssrf_sensitive_and_malformed_port():
    email = make_email(urls=(UrlMetadata("http://127.0.0.1/admin"), UrlMetadata("http://example.com:bad/x")))
    codes = {s.code for s in analyze_email_security(email, CONFIG).signals}
    assert {"SSRF_SENSITIVE_DESTINATION", "MALFORMED_URL_PORT"} <= codes


def test_attachment_policy_metadata_only():
    attachment = (AttachmentMetadata("invoice.pdf.exe", "application/pdf", size_bytes=101),)
    codes = {s.code for s in analyze_email_security(make_email(attachments=attachment), CONFIG).signals}
    assert {"DANGEROUS_EXTENSION", "DOUBLE_EXTENSION", "ATTACHMENT_SIZE_LIMIT", "MIME_EXTENSION_MISMATCH"} <= codes


def test_conflicting_or_critical_signals_fail_closed():
    analysis = analyze_email_security(make_email(urls=(UrlMetadata("http://10.0.0.1"),)), CONFIG)
    decision = decide_security(analysis, phishing_label=1, phishing_score=2.0, config=CONFIG)
    assert decision.classification is SecurityClassification.REVIEW_REQUIRED


def test_strong_ml_plus_supporting_signal_is_phishing():
    analysis = analyze_email_security(make_email(headers={"authentication-results": "spf=fail"}), CONFIG)
    decision = decide_security(analysis, phishing_label=1, phishing_score=2.0, config=CONFIG)
    assert decision.classification is SecurityClassification.PHISHING


def test_positive_ml_without_support_is_suspicious():
    decision = decide_security(analyze_email_security(make_email(), CONFIG), phishing_label=1, phishing_score=0.2, config=CONFIG)
    assert decision.classification is SecurityClassification.SUSPICIOUS


def test_unavailable_ml_fails_closed():
    decision = decide_security(analyze_email_security(make_email(), CONFIG), phishing_label=None, phishing_score=None, config=CONFIG)
    assert decision.classification is SecurityClassification.REVIEW_REQUIRED


def test_priority_gate_is_explicit():
    from src.security.eligibility import is_priority_eligible
    assert not is_priority_eligible(SecurityClassification.PHISHING)
    assert not is_priority_eligible(SecurityClassification.SUSPICIOUS)
    assert not is_priority_eligible(SecurityClassification.REVIEW_REQUIRED)
    assert is_priority_eligible(SecurityClassification.NON_PHISHING)


def test_safe_logging_drops_secrets_and_body():
    fields = sanitize_log_fields({"request_id": "r", "password": "secret", "api_key": "abc", "raw_body": "sensitive body", "message_id": "m"})
    assert fields == {"request_id": "r", "message_id": "m"}
