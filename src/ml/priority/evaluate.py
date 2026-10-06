from __future__ import annotations

from typing import Any, Iterable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

LABELS = ("P1", "P2", "P3")


def evaluate_priority_predictions(
    y_true: Iterable[str],
    y_pred: Iterable[str],
) -> dict[str, Any]:
    true = np.asarray(list(y_true))
    pred = np.asarray(list(y_pred))
    if len(true) != len(pred) or len(true) == 0:
        raise ValueError("y_true and y_pred must be non-empty and have equal length.")
    if not set(true).issubset(set(LABELS)) or not set(pred).issubset(set(LABELS)):
        raise ValueError("Priority labels must be P1/P2/P3.")

    matrix = confusion_matrix(true, pred, labels=list(LABELS))
    per_class = {}
    for label in LABELS:
        true_binary = true == label
        pred_binary = pred == label
        per_class[label] = {
            "precision": float(
                precision_score(true_binary, pred_binary, average="binary", zero_division=0)
            ),
            "recall": float(
                recall_score(true_binary, pred_binary, average="binary", zero_division=0)
            ),
            "f1": float(
                f1_score(true_binary, pred_binary, average="binary", zero_division=0)
            ),
            "support": int(np.sum(true == label)),
        }

    return {
        "accuracy": float(accuracy_score(true, pred)),
        "precision_macro": float(
            precision_score(true, pred, labels=list(LABELS), average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(true, pred, labels=list(LABELS), average="macro", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(true, pred, labels=list(LABELS), average="macro", zero_division=0)
        ),
        "precision_weighted": float(
            precision_score(true, pred, labels=list(LABELS), average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(true, pred, labels=list(LABELS), average="weighted", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(true, pred, labels=list(LABELS), average="weighted", zero_division=0)
        ),
        "confusion_matrix": matrix.tolist(),
        "labels": list(LABELS),
        "per_class": per_class,
        "metric_semantics": (
            "Macro metrics weight P1/P2/P3 equally; weighted metrics weight by class support. "
            "Labels are deterministic proxy/project labels, not human annotations."
        ),
    }
