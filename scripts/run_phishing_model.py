"""Train and evaluate the IESP Milestone 2 phishing baseline."""

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

from src.ml.phishing.evaluate import evaluate_predictions
from src.ml.phishing.predict import predict_labels, predict_scores
from src.ml.phishing.train import save_phishing_model, train_phishing_model


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)["phishing"]


def evaluate_split(model, frame: pd.DataFrame, config: dict) -> dict:
    texts = frame[config["text_column"]].astype(str)
    y_true = frame[config["label_column"]].astype(int)
    return evaluate_predictions(
        y_true,
        predict_labels(model, texts),
        predict_scores(model, texts),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/processed/train.parquet")
    parser.add_argument("--validation", default="data/processed/validation.parquet")
    parser.add_argument("--test", default="data/processed/test.parquet")
    parser.add_argument("--config", default="configs/phishing.yaml")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--metrics-output", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    train_df = pd.read_parquet(args.train)
    validation_df = pd.read_parquet(args.validation)
    test_df = pd.read_parquet(args.test)

    model = train_phishing_model(train_df, config)
    validation_metrics = evaluate_split(model, validation_df, config)
    test_metrics = evaluate_split(model, test_df, config)

    artifact = args.artifact or config["artifacts"]["pipeline"]
    _, metadata_path = save_phishing_model(
        model,
        artifact,
        metadata={
            "project": "IESP",
            "milestone": "Milestone 2",
            "model": "TF-IDF + LinearSVC",
            "text_column": config["text_column"],
            "label_column": config["label_column"],
            "training_records": len(train_df),
            "validation_records": len(validation_df),
            "test_records": len(test_df),
            "evaluation_note": (
                "Validation metrics are diagnostics. Test metrics are final "
                "held-out results for this exact training run."
            ),
            "score_semantics": "LinearSVC decision_function margin; not a probability",
        },
    )

    results = {
        "model": "TF-IDF + LinearSVC",
        "training_records": len(train_df),
        "validation": validation_metrics,
        "test": test_metrics,
        "artifact": str(artifact),
        "metadata": str(metadata_path),
    }

    if args.metrics_output:
        Path(args.metrics_output).write_text(
            json.dumps(results, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
