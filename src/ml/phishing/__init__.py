"""Milestone 2 phishing classification package."""

from .features import build_tfidf_vectorizer
from .train import build_phishing_pipeline, train_phishing_model
from .predict import predict_scores, predict_labels, load_phishing_model
from .evaluate import evaluate_predictions

__all__ = [
    "build_tfidf_vectorizer",
    "build_phishing_pipeline",
    "train_phishing_model",
    "predict_scores",
    "predict_labels",
    "load_phishing_model",
    "evaluate_predictions",
]
