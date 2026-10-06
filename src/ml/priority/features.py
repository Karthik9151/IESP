from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

DEFAULT_URGENCY_KEYWORDS = (
    "urgent", "immediately", "asap", "right away", "action required",
    "respond now", "today", "within 24 hours",
)
DEFAULT_DEADLINE_KEYWORDS = (
    "deadline", "due by", "due today", "expires", "expiration",
    "before friday", "by friday", "by end of day",
)
DEFAULT_ACTION_KEYWORDS = (
    "verify", "confirm", "review", "approve", "submit", "complete",
    "respond", "reply", "sign", "pay",
)
TIME_RE = re.compile(
    r"\b(?:\d{1,2}(?::\d{2})?\s?(?:am|pm)|\d{1,2}/\d{1,2}(?:/\d{2,4})?|"
    r"\b(?:today|tomorrow|tonight|this week|next week)\b)",
    re.I,
)
WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")


def _phrase_count(text: str, phrases: Iterable[str]) -> int:
    lower = text.lower()
    return sum(lower.count(str(phrase).lower()) for phrase in phrases if phrase)


def engineered_features(text: str, config: Mapping[str, Any] | None = None) -> dict[str, float]:
    cfg = dict(config or {})
    value = str(text or "")
    words = WORD_RE.findall(value)
    alpha = "".join(ch for ch in value if ch.isalpha())
    uppercase = sum(1 for ch in alpha if ch.isupper())
    return {
        "message_length": float(len(value)),
        "word_count": float(len(words)),
        "sentence_count": float(len(SENTENCE_RE.findall(value.strip())) if value.strip() else 0),
        "uppercase_ratio": float(uppercase / len(alpha)) if alpha else 0.0,
        "exclamation_count": float(value.count("!")),
        "question_count": float(value.count("?")),
        "urgency_keyword_count": float(
            _phrase_count(value, cfg.get("urgency_keywords", DEFAULT_URGENCY_KEYWORDS))
        ),
        "deadline_keyword_count": float(
            _phrase_count(value, cfg.get("deadline_keywords", DEFAULT_DEADLINE_KEYWORDS))
        ),
        "action_keyword_count": float(
            _phrase_count(value, cfg.get("action_keywords", DEFAULT_ACTION_KEYWORDS))
        ),
        "time_expression_indicator": float(bool(TIME_RE.search(value))),
        "numeric_indicator": float(bool(re.search(r"\b\d+(?:[.,:]\d+)?\b", value))),
    }


class VaderFeatureExtractor:
    """Extract deterministic VADER sentiment features.

    vaderSentiment is a hard dependency for M3 training/inference. This module
    does not silently substitute another sentiment implementation.
    """

    def __init__(self) -> None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        except ImportError as exc:
            raise RuntimeError(
                "vaderSentiment==3.3.2 is required for priority ML"
            ) from exc
        self._analyzer = SentimentIntensityAnalyzer()

    def transform_one(self, text: str) -> dict[str, float]:
        scores = self._analyzer.polarity_scores(str(text or ""))
        return {
            f"vader_{key}": float(scores[key])
            for key in ("compound", "pos", "neg", "neu")
        }


class PriorityFeatureTransformer(BaseEstimator, TransformerMixin):
    """Combine VADER and engineered email-urgency features into a numeric matrix."""

    FEATURE_NAMES = (
        "vader_compound", "vader_pos", "vader_neg", "vader_neu",
        "message_length", "word_count", "sentence_count", "uppercase_ratio",
        "exclamation_count", "question_count", "urgency_keyword_count",
        "deadline_keyword_count", "action_keyword_count",
        "time_expression_indicator", "numeric_indicator",
    )

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def fit(self, X, y=None):
        self.vader_ = VaderFeatureExtractor()
        self.feature_names_in_ = list(self.FEATURE_NAMES)
        return self

    def transform(self, X):
        rows = []
        for text in X:
            vader = self.vader_.transform_one(str(text or ""))
            engineered = engineered_features(str(text or ""), self.config)
            rows.append([
                vader[name] if name.startswith("vader_") else engineered[name]
                for name in self.FEATURE_NAMES
            ])
        return np.asarray(rows, dtype=float)


def extract_priority_features(text: str, config: dict | None = None) -> dict[str, float]:
    vader = VaderFeatureExtractor().transform_one(text)
    return {**vader, **engineered_features(text, config)}
