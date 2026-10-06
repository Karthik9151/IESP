from __future__ import annotations

import re

from src.domain.models import SecuritySignal, Severity

_SCRIPT_RE = re.compile(r"<\s*script\b", re.I)
_EVENT_HANDLER_RE = re.compile(r"\bon[a-z]+\s*=", re.I)
_JS_SCHEME_RE = re.compile(r"""(?:href|src)\s*=\s*["']?\s*javascript:""", re.I)
_HIDDEN_FORM_RE = re.compile(r"<\s*(?:form|input)\b", re.I)


def analyze_html(html: str) -> list[SecuritySignal]:
    """Analyze HTML structurally; never render or execute it."""
    text = str(html or "")
    signals = []
    if _SCRIPT_RE.search(text):
        signals.append(SecuritySignal("HTML_SCRIPT", Severity.HIGH, "HTML_ANOMALY", "HTML contains a script element.", {}))
    if _EVENT_HANDLER_RE.search(text):
        signals.append(SecuritySignal("HTML_EVENT_HANDLER", Severity.HIGH, "HTML_ANOMALY", "HTML contains an inline event handler.", {}))
    if _JS_SCHEME_RE.search(text):
        signals.append(SecuritySignal("HTML_JAVASCRIPT_SCHEME", Severity.HIGH, "HTML_ANOMALY", "HTML contains a javascript: URL scheme.", {}))
    if _HIDDEN_FORM_RE.search(text):
        signals.append(SecuritySignal("HTML_FORM", Severity.MEDIUM, "HTML_ANOMALY", "HTML contains a form control and should not be executed or trusted.", {}))
    return signals
