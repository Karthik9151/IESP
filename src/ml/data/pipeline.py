"""Reproducible Milestone 1 dataset preparation for IESP.

The pipeline deliberately separates structural dataset preparation from model
preprocessing. No TF-IDF, vectorizer fitting, stemming, or model training
belongs in this module.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ORIGINAL_COLUMNS = [
    "sender",
    "sender_domain",
    "receiver",
    "receiver_domain",
    "date",
    "subject",
    "content_types",
    "body",
    "urls",
    "url_count",
    "url_length_max",
    "url_length_avg",
    "url_subdom_max",
    "url_subdom_avg",
    "attachment_count",
    "has_attachments",
    "attachment_types",
    "language",
    "source",
    "label",
]

DEFAULT_SPLIT_CONFIG = {
    "train_ratio": 0.70,
    "validation_ratio": 0.15,
    "test_ratio": 0.15,
    "random_state": 42,
    "stratify": "label",
}

_ALLOWED_LABELS = {0, 1}
_HORIZONTAL_WS_RE = re.compile(r"[ \t\f\v]+")
_LINE_WS_RE = re.compile(r"[ \t]+\n|\n[ \t]+")
_BLANK_LINE_RE = re.compile(r"\n{3,}")


def normalize_text(value: Any) -> str:
    """Apply conservative, deterministic structural text normalization.

    Security-relevant tokens such as URLs, domains, numbers, punctuation,
    special characters, and placeholders are intentionally preserved.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""

    text = str(value)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = _HORIZONTAL_WS_RE.sub(" ", text)
    text = _LINE_WS_RE.sub("\n", text)
    text = _BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()


def _canonical_value(value: Any) -> Any:
    """Convert common pandas/numpy values to stable JSON-compatible values."""
    if value is None:
        return None

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        value = float(value)
        if math.isnan(value):
            return None
        return value

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }

    return value if isinstance(value, (str, int, float, bool)) else str(value)


def row_fingerprint(row: pd.Series, columns: list[str] | None = None) -> str:
    """Return a deterministic SHA-256 fingerprint for one complete record."""
    columns = columns or ORIGINAL_COLUMNS
    payload = [_canonical_value(row[column]) for column in columns]
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def project_fingerprint(frame: pd.DataFrame) -> str:
    """Hash sorted record fingerprints to produce a dataset-level fingerprint."""
    values = sorted(str(value) for value in frame["record_fingerprint"])
    payload = "\n".join(values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def split_fingerprint(frame: pd.DataFrame) -> str:
    """Hash the ordered record-fingerprint sequence for a split."""
    values = "\n".join(str(value) for value in frame["record_fingerprint"])
    return hashlib.sha256(values.encode("utf-8")).hexdigest()


def validate_schema(frame: pd.DataFrame) -> None:
    """Fail fast when any authoritative source column is missing."""
    missing = [column for column in ORIGINAL_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required dataset columns: {missing}")


def validate_labels(frame: pd.DataFrame, label_column: str = "label") -> None:
    """Validate that all usable labels are exactly 0 or 1."""
    labels = set(frame[label_column].dropna().astype(int).unique().tolist())
    unexpected = sorted(labels - _ALLOWED_LABELS)
    if unexpected:
        raise ValueError(f"Unexpected labels found: {unexpected}")

    non_integer = frame[label_column].dropna().apply(float).apply(float.is_integer)
    if not non_integer.all():
        raise ValueError("Labels must be integer-valued 0/1 labels.")


def prepare_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Create the final structurally prepared dataset.

    Processing order:
      1. Validate original schema.
      2. Count raw rows.
      3. Remove only rows missing label or body.
      4. Validate labels.
      5. Fingerprint complete original records.
      6. Remove exact duplicate full records.
      7. Preserve raw body as text_raw.
      8. Add conservative normalized text as text_normalized.
    """
    validate_schema(frame)
    working = frame.copy()

    raw_rows = len(working)
    missing_label = int(working["label"].isna().sum())
    missing_body = int(working["body"].isna().sum())

    working = working.dropna(subset=["label", "body"]).copy()
    working["label"] = working["label"].astype(int)
    validate_labels(working)

    working["record_fingerprint"] = working.apply(
        row_fingerprint,
        axis=1,
        result_type="reduce",
    )

    before_dedup = len(working)
    working = working.drop_duplicates(
        subset=["record_fingerprint"],
        keep="first",
    ).copy()
    duplicate_copies = before_dedup - len(working)

    working["text_raw"] = working["body"].astype(str)
    working["text_normalized"] = working["text_raw"].map(normalize_text)

    summary = {
        "raw_records": raw_rows,
        "missing_label_records": missing_label,
        "missing_body_records": missing_body,
        "usable_labeled_text_records": before_dedup,
        "exact_duplicate_copies": duplicate_copies,
        "final_unique_records": len(working),
    }
    return working, summary


def split_dataset(
    frame: pd.DataFrame,
    *,
    train_ratio: float = DEFAULT_SPLIT_CONFIG["train_ratio"],
    validation_ratio: float = DEFAULT_SPLIT_CONFIG["validation_ratio"],
    test_ratio: float = DEFAULT_SPLIT_CONFIG["test_ratio"],
    random_state: int = DEFAULT_SPLIT_CONFIG["random_state"],
    stratify_column: str = DEFAULT_SPLIT_CONFIG["stratify"],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create a deterministic 70/15/15 stratified split."""
    total = train_ratio + validation_ratio + test_ratio
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError("train_ratio + validation_ratio + test_ratio must equal 1.")

    train_df, temp_df = train_test_split(
        frame,
        test_size=(validation_ratio + test_ratio),
        random_state=random_state,
        stratify=frame[stratify_column],
    )

    validation_fraction_of_temp = validation_ratio / (validation_ratio + test_ratio)
    validation_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - validation_fraction_of_temp),
        random_state=random_state,
        stratify=temp_df[stratify_column],
    )

    return train_df.copy(), validation_df.copy(), test_df.copy()


def validate_split_integrity(
    full_df: pd.DataFrame,
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """Verify conservation and exact fingerprint separation across splits."""
    split_frames = [train_df, validation_df, test_df]

    total_rows = sum(len(frame) for frame in split_frames)
    if total_rows != len(full_df):
        raise AssertionError(
            f"Split record conservation failed: {total_rows} != {len(full_df)}"
        )

    full_fps = set(full_df["record_fingerprint"])
    split_fps = [set(frame["record_fingerprint"]) for frame in split_frames]
    union = set().union(*split_fps)

    if union != full_fps:
        raise AssertionError("Split coverage does not equal the final dataset.")

    if len(union) != total_rows:
        raise AssertionError("A record fingerprint occurs more than once across splits.")

    if split_fps[0] & split_fps[1]:
        raise AssertionError("Train/validation fingerprint overlap detected.")
    if split_fps[0] & split_fps[2]:
        raise AssertionError("Train/test fingerprint overlap detected.")
    if split_fps[1] & split_fps[2]:
        raise AssertionError("Validation/test fingerprint overlap detected.")


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """Return auditable counts and class distribution for a dataset frame."""
    counts = frame["label"].value_counts().sort_index()
    total = len(frame)
    return {
        "records": total,
        "benign": int(counts.get(0, 0)),
        "phishing": int(counts.get(1, 0)),
        "benign_percent": round(float(counts.get(0, 0) / total * 100), 4)
        if total
        else 0.0,
        "phishing_percent": round(float(counts.get(1, 0) / total * 100), 4)
        if total
        else 0.0,
    }


def write_outputs(
    full_df: pd.DataFrame,
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str | Path,
) -> dict[str, str]:
    """Write processed data and return their paths.

    The repository .gitignore intentionally excludes these generated data files.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    paths = {
        "full": directory / "meajor_ml.parquet",
        "train": directory / "train.parquet",
        "validation": directory / "validation.parquet",
        "test": directory / "test.parquet",
    }

    full_df.to_parquet(paths["full"], index=False, compression="gzip")
    train_df.to_parquet(paths["train"], index=False, compression="gzip")
    validation_df.to_parquet(paths["validation"], index=False, compression="gzip")
    test_df.to_parquet(paths["test"], index=False, compression="gzip")

    return {key: str(path) for key, path in paths.items()}
