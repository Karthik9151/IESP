"""Inference helpers for the Milestone 2 phishing model."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
from sklearn.pipeline import Pipeline


def load_phishing_model(path: str | Path) -> Pipeline:
    """Load a persisted phishing pipeline."""
    return joblib.load(path)


def predict_scores(model: Pipeline, texts: Iterable[str]):
    """Return raw LinearSVC decision scores.

    These scores are margins, not probabilities. The function deliberately
    exposes them as scores so callers cannot mistake them for calibrated
    probabilities.
    """
    return model.decision_function(list(texts))


def predict_labels(model: Pipeline, texts: Iterable[str]):
    """Return predicted labels (0 = benign, 1 = phishing)."""
    return model.predict(list(texts))
