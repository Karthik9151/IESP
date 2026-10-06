from __future__ import annotations

from email.utils import parseaddr

from src.domain.models import EmailMessage, SecuritySignal, Severity


def _domain(value: str) -> str:
    address = parseaddr(value or "")[1].strip().lower()
    return address.rsplit("@", 1)[1].rstrip(".") if "@" in address else ""


def _signal(code, severity, message, **evidence):
    return SecuritySignal(code, severity, "HEADER_ANOMALY", message, evidence)


def analyze_headers(email: EmailMessage) -> list[SecuritySignal]:
    headers = email.headers.values
    from_domain = email.sender.domain.lower().rstrip(".")
    return_path_domain = _domain(headers.get("return-path", ""))
    reply_domain = _domain(headers.get("reply-to", ""))
    signals = []
    if return_path_domain and from_domain and return_path_domain != from_domain:
        signals.append(_signal("FROM_RETURN_PATH_MISMATCH", Severity.MEDIUM, "From and Return-Path domains differ.", from_domain=from_domain, return_path_domain=return_path_domain))
    if reply_domain and from_domain and reply_domain != from_domain:
        signals.append(_signal("FROM_REPLY_TO_MISMATCH", Severity.MEDIUM, "From and Reply-To domains differ.", from_domain=from_domain, reply_to_domain=reply_domain))
    auth = headers.get("authentication-results", "").lower()
    if any(x in auth for x in ("spf=fail", "dkim=fail", "dmarc=fail")):
        signals.append(_signal("AUTHENTICATION_FAILURE", Severity.HIGH, "Authentication-Results contains an SPF, DKIM, or DMARC failure.", header="authentication-results"))
    received_spf = headers.get("received-spf", "").lower()
    if "fail" in received_spf or "softfail" in received_spf:
        signals.append(_signal("SPF_FAILURE", Severity.HIGH, "Received-SPF indicates failure.", header="received-spf"))
    return signals
