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
from src.ml.phishing.predict import load_phishing_model, predict_labels, predict_scores
from src.ml.phishing.train import save_phishing_model, train_phishing_model


EXPECTED_M1_FINGERPRINT = "34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582"
EXPECTED_SPLITS = {"train": 76069, "validation": 16300, "test": 16301}


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


def _assert_prediction_equivalence(model_a, model_b, frame: pd.DataFrame, config: dict) -> None:
    texts = frame[config["text_column"]].astype(str)
    labels_a = predict_labels(model_a, texts)
    labels_b = predict_labels(model_b, texts)
    scores_a = predict_scores(model_a, texts)
    scores_b = predict_scores(model_b, texts)
    if not (labels_a == labels_b).all():
        raise RuntimeError("Determinism gate failed: label predictions differ between runs.")
    if not (abs(scores_a - scores_b) < 1e-12).all():
        raise RuntimeError("Determinism gate failed: decision scores differ between runs.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/processed/train.parquet")
    parser.add_argument("--validation", default="data/processed/validation.parquet")
    parser.add_argument("--test", default="data/processed/test.parquet")
    parser.add_argument("--config", default="configs/phishing.yaml")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--metrics-output", default=None)
    parser.add_argument("--manifest", default="data/processed/dataset_manifest.json")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"M1 manifest not found: {manifest_path}. Run the accepted M1 pipeline first."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("project_fingerprint") != EXPECTED_M1_FINGERPRINT:
        raise RuntimeError("M1 fingerprint gate failed; refusing to train M2.")
    for name, expected in EXPECTED_SPLITS.items():
        actual = manifest.get("splits", {}).get(name, {}).get("records")
        if actual != expected:
            raise RuntimeError(
                f"M1 {name} split count gate failed: expected {expected}, got {actual}."
            )

    train_df = pd.read_parquet(args.train)
    validation_df = pd.read_parquet(args.validation)
    test_df = pd.read_parquet(args.test)

    model = train_phishing_model(train_df, config)
    validation_metrics = evaluate_split(model, validation_df, config)
    test_metrics = evaluate_split(model, test_df, config)

    # Deterministic second training/inference check required by the M2 acceptance gate.
    second_model = train_phishing_model(train_df, config)
    _assert_prediction_equivalence(model, second_model, validation_df, config)
    _assert_prediction_equivalence(model, second_model, test_df, config)

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
            "determinism_check": "second training + held-out label/score equivalence",
            "evaluation_note": (
                "Validation metrics are diagnostics. Test metrics are final "
                "held-out results for this exact training run."
            ),
            "score_semantics": "LinearSVC decision_function margin; not a probability",
        },
    )

    # Persistence gate: loaded artifact must reproduce predictions.
    loaded_model = load_phishing_model(artifact)
    _assert_prediction_equivalence(model, loaded_model, test_df, config)

    results = {
        "model": "TF-IDF + LinearSVC",
        "training_records": len(train_df),
        "validation": validation_metrics,
        "test": test_metrics,
        "determinism_check": "PASS",
        "persistence_check": "PASS",
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
