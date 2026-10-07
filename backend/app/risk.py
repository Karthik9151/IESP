from __future__ import annotations

from collections.abc import Iterable

_BASE = {
    "PHISHING": 90.0,
    "SUSPICIOUS": 65.0,
    "REVIEW REQUIRED": 45.0,
    "NON-PHISHING": 10.0,
}
_SEVERITY_BONUS = {"CRITICAL": 10.0, "HIGH": 7.0, "MEDIUM": 4.0, "LOW": 2.0, "INFO": 0.0}


def policy_risk_score(classification: str, reasons: Iterable[dict]) -> float:
    """Return IESP's deterministic policy score; this is not a probability."""
    base = _BASE.get(classification, 50.0)
    bonus = sum(_SEVERITY_BONUS.get(str(item.get("severity")), 0.0) for item in reasons)
    return min(100.0, base + min(10.0, bonus))
