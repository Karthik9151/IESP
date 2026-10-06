from __future__ import annotations

from src.domain.models import AnalysisResult, SecurityClassification, SecurityDecision, SecuritySignal, Severity
from src.parsing.email_parser import EmailParseError, parse_email_bytes
from .engine import SecurityEngine


def analyze_raw_email(engine: SecurityEngine, raw_message: bytes, *, request_id: str | None = None) -> AnalysisResult:
    try:
        email = parse_email_bytes(raw_message, max_bytes=int(engine.config.get("parser", {}).get("max_bytes", 2_000_000)))
    except EmailParseError as exc:
        reason = SecuritySignal("PARSER_ERROR", Severity.CRITICAL, "PARSER_ERROR", "Email could not be parsed safely; manual review is required.", {"error_type": type(exc).__name__})
        return AnalysisResult("unparsed", SecurityDecision(SecurityClassification.REVIEW_REQUIRED, (reason,)), None, request_id)
    return engine.analyze(email, request_id=request_id)
