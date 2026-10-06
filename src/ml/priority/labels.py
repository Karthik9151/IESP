from __future__ import annotations

from typing import Any, Mapping

from .features import engineered_features

DEFAULT_POLICY = {"p1_threshold": 4, "p2_threshold": 2}


def proxy_score(text: str, config: Mapping[str, Any] | None = None) -> int:
    cfg = dict(config or {})
    features = engineered_features(text, cfg)
    score = (
        (2 if features["urgency_keyword_count"] > 0 else 0)
        + (1 if features["deadline_keyword_count"] > 0 else 0)
        + (1 if features["action_keyword_count"] > 0 else 0)
        + (1 if features["time_expression_indicator"] else 0)
        + (1 if features["numeric_indicator"] and features["deadline_keyword_count"] > 0 else 0)
    )
    lower = str(text or "").lower()
    if any(term in lower for term in ("critical", "security incident", "outage", "breach", "fraud")):
        score += 2
    if any(term in lower for term in ("payment", "invoice", "transfer", "account overdue", "past due")):
        score += 1
    return int(score)


def generate_proxy_label(text: str, config: Mapping[str, Any] | None = None) -> str:
    cfg = {**DEFAULT_POLICY, **dict(config or {})}
    score = proxy_score(text, cfg)
    if score >= int(cfg["p1_threshold"]):
        return "P1"
    if score >= int(cfg["p2_threshold"]):
        return "P2"
    return "P3"


def generate_proxy_labels(texts, config=None):
    return [generate_proxy_label(text, config) for text in texts]
