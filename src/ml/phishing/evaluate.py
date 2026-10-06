"""Held-out evaluation for the Milestone 2 phishing baseline."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_predictions(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    decision_scores: Iterable[float],
) -> dict[str, Any]:
    """Calculate the required phishing metrics.

    Class 1 is phishing. decision_scores must be the raw SVM decision
    function output; it is suitable for ranking-based ROC/PR metrics but is
    not a probability.
    """
    y_true = np.asarray(list(y_true), dtype=int)
    y_pred = np.asarray(list(y_pred), dtype=int)
    scores = np.asarray(list(decision_scores), dtype=float)

    if not (len(y_true) == len(y_pred) == len(scores)):
        raise ValueError("y_true, y_pred, and decision_scores must have equal length.")
    if len(y_true) == 0:
        raise ValueError("Cannot evaluate an empty prediction set.")
    if not set(y_true).issubset({0, 1}):
        raise ValueError("y_true must contain only labels 0 and 1.")
    if not set(y_pred).issubset({0, 1}):
        raise ValueError("y_pred must contain only labels 0 and 1.")

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = (int(value) for value in cm.ravel())

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "confusion_matrix": cm.tolist(),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "positive_class": "phishing (1)",
        "score_semantics": "LinearSVC decision_function margin; not a probability",
    }
}
