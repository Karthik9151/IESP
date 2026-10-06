"""Run the IESP Milestone 1 dataset pipeline locally or in Colab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from src.ml.data.pipeline import (
    prepare_dataset,
    project_fingerprint,
    split_dataset,
    split_fingerprint,
    summarize,
    validate_split_integrity,
    validate_schema,
)


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_manifest(
    config: dict,
    source_path: str,
    full_df: pd.DataFrame,
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preparation_summary: dict,
) -> dict:
    return {
        "project": "IESP",
        "milestone": "Milestone 1",
        "dataset": config["dataset"],
        "source_path": source_path,
        "preparation": preparation_summary,
        "final_summary": summarize(full_df),
        "splits": {
            "configuration": config["dataset"]["split"],
            "train": {
                "records": len(train_df),
                "summary": summarize(train_df),
                "fingerprint": split_fingerprint(train_df),
            },
            "validation": {
                "records": len(validation_df),
                "summary": summarize(validation_df),
                "fingerprint": split_fingerprint(validation_df),
            },
            "test": {
                "records": len(test_df),
                "summary": summarize(test_df),
                "fingerprint": split_fingerprint(test_df),
            },
        },
        "project_fingerprint": project_fingerprint(full_df),
        "preprocessing_boundary": (
            "Structural cleaning/validation and exact deduplication happen before "
            "splitting. Model preprocessing such as TF-IDF must be fitted only on "
            "the training set and then used to transform validation/test."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the MeAJOR parquet file.")
    parser.add_argument(
        "--config",
        default="configs/dataset.yaml",
        help="Path to the dataset configuration YAML.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory; defaults to config value.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    dataset_cfg = config["dataset"]
    output_dir = args.output_dir or dataset_cfg["output"]["directory"]

    source_path = str(Path(args.input).resolve())
    raw_df = pd.read_parquet(source_path)

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
    output_paths = write_outputs(
        final_df,
        train_df,
        validation_df,
        test_df,
        output_dir,
    )

    manifest = build_manifest(
        config,
        source_path,
        final_df,
        train_df,
        validation_df,
        test_df,
        preparation_summary,
    )

    manifest_path = Path(output_dir) / dataset_cfg["output"]["manifest"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("IESP — Milestone 1 dataset pipeline")
    print(f"Raw records: {preparation_summary['raw_records']}")
    print(f"Usable labeled-text records: {preparation_summary['usable_labeled_text_records']}")
    print(f"Exact duplicate copies: {preparation_summary['exact_duplicate_copies']}")
    print(f"Final unique records: {preparation_summary['final_unique_records']}")
    print(f"Train: {len(train_df)}")
    print(f"Validation: {len(validation_df)}")
    print(f"Test: {len(test_df)}")
    print(f"Project fingerprint: {manifest['project_fingerprint']}")
    print(f"Manifest: {manifest_path}")

    for name, path in output_paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
