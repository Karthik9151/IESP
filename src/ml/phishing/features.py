"""Leakage-safe TF-IDF feature construction for phishing classification."""

from __future__ import annotations

from typing import Any, Mapping

from sklearn.feature_extraction.text import TfidfVectorizer


def build_tfidf_vectorizer(config: Mapping[str, Any] | None = None) -> TfidfVectorizer:
    """Build a deterministic TF-IDF vectorizer from configuration.

    The vectorizer is only fitted when the training pipeline is fitted. This
    module never fits on validation or test data.
    """
    cfg = dict(config or {})
    ngram_range = tuple(cfg.get("ngram_range", [1, 2]))

    return TfidfVectorizer(
        lowercase=bool(cfg.get("lowercase", True)),
        strip_accents=cfg.get("strip_accents", "unicode"),
        ngram_range=ngram_range,
        min_df=cfg.get("min_df", 2),
        max_df=cfg.get("max_df", 0.98),
        sublinear_tf=bool(cfg.get("sublinear_tf", True)),
        max_features=cfg.get("max_features"),
        analyzer=cfg.get("analyzer", "word"),
    )


def validate_feature_frame(frame, text_column: str = "text_normalized", label_column: str = "label") -> None:
    """Validate the minimum schema required by the phishing model."""
    missing = [column for column in (text_column, label_column) if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing phishing model columns: {missing}")

    labels = set(frame[label_column].dropna().astype(int).unique().tolist())
    if not labels.issubset({0, 1}):
        raise ValueError(f"Unexpected phishing labels: {sorted(labels - {0, 1})}")

    if frame[text_column].isna().any():
        raise ValueError(f"{text_column} contains missing values.")
