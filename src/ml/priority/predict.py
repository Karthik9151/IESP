from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from src.domain.models import PriorityLabel, PriorityResult


def load_priority_model(path: str | Path) -> Pipeline:
    return joblib.load(path)


def predict_priority(model: Pipeline, text: str) -> PriorityResult:
    label = str(model.predict([text])[0])
    probabilities = model.predict_proba([text])[0] if hasattr(model, "predict_proba") else []
    classes = (
        list(model.named_steps.get("logistic").classes_)
        if hasattr(model, "named_steps") and "logistic" in model.named_steps
        else []
    )
    scores = {str(cls): float(score) for cls, score in zip(classes, probabilities)}
    return PriorityResult(
        label=PriorityLabel(label),
        proxy_label=True,
        score_by_class=scores,
    )
