"""Run full Milestone 2 acceptance from the authoritative MeAJOR Parquet file.

This command performs the accepted Milestone 1 preparation, verifies the
accepted dataset fingerprint/split sizes, fits TF-IDF + LinearSVC on train
only, evaluates validation/test separately, checks fitted-vocabulary stability,
checks deterministic retraining, and writes model/evaluation artifacts.

No sampling or artificial row limit is applied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ml.data.pipeline import (
    prepare_dataset,
    project_fingerprint,
    split_dataset,
    split_fingerprint,
    validate_schema,
    validate_split_integrity,
    write_outputs,
)
from src.ml.phishing.evaluate import evaluate_predictions
from src.ml.phishing.predict import predict_labels, predict_scores
from src.ml.phishing.train import save_phishing_model, train_phishing_model


EXPECTED_PROJECT_FINGERPRINT = (
    "34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582"
)
EXPECTED_SPLIT_RECORDS = {
    "train": 76069,
    "validation": 16300,
    "test": 16301,
}


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def evaluate_split(model, frame: pd.DataFrame, config: dict) -> dict:
    text_column = config["text_column"]
    label_column = config["label_column"]
    texts = frame[text_column].astype(str)
    y_true = frame[label_column].astype(int)
    return evaluate_predictions(
        y_true,
        predict_labels(model, texts),
        predict_scores(model, texts),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_fitted_features(model, train_df, validation_df, test_df, config):
    text_column = config["text_column"]
    vectorizer = model.named_steps["tfidf"]

    vocabulary_before = dict(vectorizer.vocabulary_)
    idf_before = np.asarray(vectorizer.idf_).copy()

    train_matrix = vectorizer.transform(train_df[text_column].astype(str))
    validation_matrix = vectorizer.transform(validation_df[text_column].astype(str))
    test_matrix = vectorizer.transform(test_df[text_column].astype(str))

    vocabulary_after = dict(vectorizer.vocabulary_)
    idf_after = np.asarray(vectorizer.idf_)

    vocabulary_stable = vocabulary_before == vocabulary_after
    idf_stable = np.array_equal(idf_before, idf_after)

    if not vocabulary_stable or not idf_stable:
        raise AssertionError(
            "Validation/test transformation changed fitted TF-IDF state."
        )

    return {
        "fit_split": "train",
        "transform_splits": ["train", "validation", "test"],
        "vocabulary_size": len(vocabulary_before),
        "train_matrix_shape": list(train_matrix.shape),
        "validation_matrix_shape": list(validation_matrix.shape),
        "test_matrix_shape": list(test_matrix.shape),
        "vocabulary_stable_after_validation_test_transform": vocabulary_stable,
        "idf_stable_after_validation_test_transform": idf_stable,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, help="Path to authoritative MeAJOR Parquet."
    )
    parser.add_argument("--dataset-config", default="configs/dataset.yaml")
    parser.add_argument("--phishing-config", default="configs/phishing.yaml")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument(
        "--artifact", default="models/phishing/phishing_pipeline.joblib"
    )
    parser.add_argument(
        "--metrics-output", default="models/phishing/m2_acceptance.json"
    )
    args = parser.parse_args()

    dataset_cfg = load_config(args.dataset_config)["dataset"]
    phishing_cfg = load_config(args.phishing_config)["phishing"]

    raw_df = pd.read_parquet(args.input)
    validate_schema(raw_df)

    final_df, preparation_summary = prepare_dataset(raw_df)
    split_cfg = dataset_cfg["split"]
    train_df, validation_df, test_df = split_dataset(
        final_df,
        train_ratio=float(split_cfg["train_ratio"]),
        validation_ratio=float(split_cfg["validation_ratio"]),
        test_ratio=float(split_cfg["test_ratio"]),
        random_state=int(split_cfg["random_state"]),
        stratify_column=str(split_cfg["stratify"]),
    )
    validate_split_integrity(final_df, train_df, validation_df, test_df)

    dataset_fingerprint = project_fingerprint(final_df)
    if dataset_fingerprint != EXPECTED_PROJECT_FINGERPRINT:
        raise RuntimeError(
            "Accepted M1 fingerprint gate failed: "
            f"expected {EXPECTED_PROJECT_FINGERPRINT}, got {dataset_fingerprint}"
        )

    actual_split_counts = {
        "train": len(train_df),
        "validation": len(validation_df),
        "test": len(test_df),
    }
    if actual_split_counts != EXPECTED_SPLIT_RECORDS:
        raise RuntimeError(
            "Accepted M1 split-count gate failed: "
            f"expected {EXPECTED_SPLIT_RECORDS}, got {actual_split_counts}"
        )

    output_dir = Path(args.output_dir)
    output_paths = write_outputs(
        final_df,
        train_df,
        validation_df,
        test_df,
        output_dir,
    )

    model = train_phishing_model(train_df, phishing_cfg)
    validation_metrics = evaluate_split(model, validation_df, phishing_cfg)
    test_metrics = evaluate_split(model, test_df, phishing_cfg)
    feature_audit = audit_fitted_features(
        model, train_df, validation_df, test_df, phishing_cfg
    )

    artifact_path = Path(args.artifact)
    artifact_path, metadata_path = save_phishing_model(
        model,
        artifact_path,
        metadata={
            "project": "IESP",
            "milestone": "Milestone 2",
            "dataset": "MeAJOR",
            "dataset_project_fingerprint": dataset_fingerprint,
            "training_records": len(train_df),
            "validation_records": len(validation_df),
            "test_records": len(test_df),
            "text_column": phishing_cfg["text_column"],
            "label_column": phishing_cfg["label_column"],
            "model": "TF-IDF + LinearSVC",
            "evaluation_note": (
                "Validation metrics are diagnostics; test metrics are final "
                "held-out results for this exact training run."
            ),
            "score_semantics": (
                "LinearSVC decision_function margin; not a probability"
            ),
            "feature_audit": feature_audit,
        },
    )

    model_again = train_phishing_model(train_df, phishing_cfg)
    first_labels = predict_labels(model, test_df[phishing_cfg["text_column"]])
    second_labels = predict_labels(
        model_again, test_df[phishing_cfg["text_column"]]
    )
    first_scores = predict_scores(model, test_df[phishing_cfg["text_column"]])
    second_scores = predict_scores(
        model_again, test_df[phishing_cfg["text_column"]]
    )

    labels_equal = np.array_equal(first_labels, second_labels)
    scores_equal = np.allclose(first_scores, second_scores, rtol=0, atol=0)
    if not labels_equal or not scores_equal:
        raise AssertionError("Deterministic retraining check failed.")

    retrain_check = {
        "status": "PASS",
        "labels_equal": True,
        "scores_equal": True,
    }

    artifact_sha256 = sha256_file(artifact_path)

    results = {
        "milestone": "Milestone 2",
        "acceptance_status": "PASS",
        "dataset": {
            "source_path": str(Path(args.input).resolve()),
            "raw_records": preparation_summary["raw_records"],
            "usable_labeled_text_records": preparation_summary[
                "usable_labeled_text_records"
            ],
            "exact_duplicate_copies": preparation_summary["exact_duplicate_copies"],
            "final_unique_records": preparation_summary["final_unique_records"],
            "project_fingerprint": dataset_fingerprint,
        },
        "splits": {
            name: {
                "records": actual_split_counts[name],
                "fingerprint": split_fingerprint(frame),
            }
            for name, frame in (
                ("train", train_df),
                ("validation", validation_df),
                ("test", test_df),
            )
        },
        "feature_audit": feature_audit,
        "validation": validation_metrics,
        "test": test_metrics,
        "deterministic_retraining": retrain_check,
        "artifact": {
            "path": str(artifact_path),
            "metadata_path": str(metadata_path),
            "sha256": artifact_sha256,
        },
        "generated_data": {key: str(value) for key, value in output_paths.items()},
    }

    metrics_path = Path(args.metrics_output)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Acceptance report: {metrics_path}")


if __name__ == "__main__":
    main()
