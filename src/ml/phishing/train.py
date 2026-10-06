"""Training utilities for the Milestone 2 TF-IDF + linear SVM baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .features import build_tfidf_vectorizer, validate_feature_frame


def build_phishing_pipeline(config: Mapping[str, Any] | None = None) -> Pipeline:
    """Create the complete TF-IDF + LinearSVC pipeline.

    Calling fit on this pipeline with the training split fits TF-IDF vocabulary
    and IDF weights from training text only. Validation/test text is only
    transformed after the pipeline has been fitted.
    """
    cfg = dict(config or {})
    feature_cfg = cfg.get("features", cfg)
    model_cfg = cfg.get("model", {})

    vectorizer = build_tfidf_vectorizer(feature_cfg)
    classifier = LinearSVC(
        C=float(model_cfg.get("C", 1.0)),
        class_weight=model_cfg.get("class_weight"),
        max_iter=int(model_cfg.get("max_iter", 5000)),
        random_state=int(model_cfg.get("random_state", 42)),
    )

    return Pipeline([
        ("tfidf", vectorizer),
        ("svm", classifier),
    ])


def train_phishing_model(
    train_df: pd.DataFrame,
    config: Mapping[str, Any] | None = None,
) -> Pipeline:
    """Fit the phishing pipeline using the supplied TRAINING frame only."""
    cfg = dict(config or {})
    text_column = cfg.get("text_column", "text_normalized")
    label_column = cfg.get("label_column", "label")
    validate_feature_frame(train_df, text_column, label_column)

    model = build_phishing_pipeline(cfg)
    model.fit(train_df[text_column].astype(str), train_df[label_column].astype(int))
    return model


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_phishing_model(
    model: Pipeline,
    artifact_path: str | Path,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Persist the model and an integrity-verifiable JSON metadata record."""
    artifact = Path(artifact_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact, compress=3)

    metadata_path = artifact.with_name("metadata.json")
    payload = dict(metadata or {})
    payload.setdefault("artifact", artifact.name)
    payload.setdefault("artifact_size_bytes", artifact.stat().st_size)
    payload.setdefault("artifact_sha256", _sha256_file(artifact))
    payload.setdefault("sklearn_version", sklearn.__version__)
    metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact, metadata_path
