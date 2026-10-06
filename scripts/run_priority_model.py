"""Train and evaluate the IESP Milestone 3 priority baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import yaml

from src.ml.priority.evaluate import evaluate_priority_predictions
from src.ml.priority.labels import generate_proxy_labels
from src.ml.priority.predict import predict_priority
from src.ml.priority.train import save_priority_model, train_priority_model


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["priority"]


def evaluate_split(model, frame: pd.DataFrame, config: dict) -> dict:
    texts = frame[config["text_column"]].astype(str).tolist()
    y_true = generate_proxy_labels(texts, config.get("proxy_labels", {}))
    y_pred = [predict_priority(model, text).label.value for text in texts]
    return evaluate_priority_predictions(y_true, y_pred)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/processed/train.parquet")
    parser.add_argument("--validation", default="data/processed/validation.parquet")
    parser.add_argument("--test", default="data/processed/test.parquet")
    parser.add_argument("--config", default="configs/priority.yaml")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--metrics-output", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    frames = {
        name: pd.read_parquet(path)
        for name, path in (
            ("train", args.train),
            ("validation", args.validation),
            ("test", args.test),
        )
    }
    for name, frame in frames.items():
        if config["text_column"] not in frame.columns:
            raise ValueError(f"Missing priority text column in {name}: {config['text_column']}")

    model = train_priority_model(frames["train"], config)
    validation = evaluate_split(model, frames["validation"], config)
    test = evaluate_split(model, frames["test"], config)

    artifact = args.artifact or config["artifacts"]["pipeline"]
    _, metadata_path = save_priority_model(
        model,
        artifact,
        metadata={
            "project": "IESP",
            "milestone": "Milestone 3",
            "model": "VADER + engineered features + LogisticRegression",
            "proxy_labels": True,
            "label_semantics": "P1 highest urgency, P2 medium urgency, P3 lowest urgency",
            "evaluation_note": (
                "Metrics measure agreement with deterministic proxy labels, "
                "not human urgency judgments."
            ),
        },
    )

    results = {
        "model": "VADER + engineered features + LogisticRegression",
        "training_records": len(frames["train"]),
        "validation": validation,
        "test": test,
        "artifact": str(artifact),
        "metadata": str(metadata_path),
    }
    if args.metrics_output:
        Path(args.metrics_output).write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
