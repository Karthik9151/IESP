from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Any

import joblib
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .features import PriorityFeatureTransformer
from .labels import generate_proxy_label


def build_priority_pipeline(config: Mapping[str, Any] | None = None) -> Pipeline:
    cfg = dict(config or {})
    model_cfg = cfg.get("model", {})
    classifier = LogisticRegression(
        C=float(model_cfg.get("C", 1.0)),
        max_iter=int(model_cfg.get("max_iter", 1000)),
        class_weight=model_cfg.get("class_weight"),
        random_state=int(model_cfg.get("random_state", 42)),
        solver=model_cfg.get("solver", "lbfgs"),
        multi_class=model_cfg.get("multi_class", "auto"),
    )
    return Pipeline([
        ("features", PriorityFeatureTransformer(config=cfg.get("features", cfg))),
        ("logistic", classifier),
    ])


def train_priority_model(train_df: pd.DataFrame, config: Mapping[str, Any] | None = None) -> Pipeline:
    cfg = dict(config or {})
    text_column = cfg.get("text_column", "text_normalized")
    if text_column not in train_df.columns:
        raise ValueError(f"Missing priority model column: {text_column}")
    texts = train_df[text_column].astype(str).tolist()
    labels = [generate_proxy_label(text, cfg.get("proxy_labels", {})) for text in texts]
    if len(set(labels)) < 2:
        raise ValueError(
            "Proxy-label policy produced only one class in training data; "
            "adjust data or policy transparently."
        )
    model = build_priority_pipeline(cfg)
    model.fit(texts, labels)
    return model


def save_priority_model(
    model: Pipeline,
    artifact_path: str | Path,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    artifact = Path(artifact_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact, compress=3)
    metadata_path = artifact.with_name("metadata.json")
    payload = dict(metadata or {})
    payload.setdefault("artifact", artifact.name)
    payload.setdefault("sklearn_version", sklearn.__version__)
    metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact, metadata_path
