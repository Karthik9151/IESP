from __future__ import annotations

from src.domain.models import EmailMessage, SecurityAnalysis, SecuritySignal, Severity
from .attachment_analysis import analyze_attachments
from .header_analysis import analyze_headers
from .html_analysis import analyze_html
from .url_analysis import analyze_urls


def analyze_email_security(email: EmailMessage, config: dict | None = None, *, parser_ok: bool = True) -> SecurityAnalysis:
    if not parser_ok:
        return SecurityAnalysis((SecuritySignal("PARSER_ERROR", Severity.CRITICAL, "PARSER_ERROR", "Email parsing did not complete safely.", {}),), parser_ok=False)
    cfg = config or {}
    signals = []
    signals.extend(analyze_headers(email))
    signals.extend(analyze_urls(email.urls, cfg.get("url", {})))
    signals.extend(analyze_attachments(email.attachments, cfg.get("attachment", {})))
    signals.extend(analyze_html(email.html_body))
    return SecurityAnalysis(tuple(signals), parser_ok=True)
