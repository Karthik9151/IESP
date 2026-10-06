from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import bootstrap_models


def _manifest(phishing: bytes, priority: bytes) -> dict:
    def info(filename: str, payload: bytes) -> dict:
        return {
            "filename": filename,
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    return {
        "project": "IESP",
        "release_tag": "models-v1",
        "m1_contract": {
            "project_fingerprint": bootstrap_models.EXPECTED_FINGERPRINT,
            "train_records": 76069,
            "validation_records": 16300,
            "test_records": 16301,
        },
        "models": {
            "phishing": info("phishing_pipeline.joblib", phishing),
            "priority": info("priority_pipeline.joblib", priority),
        },
    }


def test_bootstrap_reuses_verified_existing_artifacts(tmp_path: Path) -> None:
    phishing = b"phishing-model"
    priority = b"priority-model"
    root = tmp_path / "models"
    (root / "phishing").mkdir(parents=True)
    (root / "priority").mkdir(parents=True)
    (root / "phishing" / "phishing_pipeline.joblib").write_bytes(phishing)
    (root / "priority" / "priority_pipeline.joblib").write_bytes(priority)
    (root / "model-manifest.json").write_text(
        json.dumps(_manifest(phishing, priority)),
        encoding="utf-8",
    )

    bootstrap_models.bootstrap(root)

    assert (root / "phishing" / "phishing_pipeline.joblib").read_bytes() == phishing
    assert (root / "priority" / "priority_pipeline.joblib").read_bytes() == priority


def test_manifest_validation_rejects_wrong_m1_contract() -> None:
    manifest = _manifest(b"p", b"q")
    manifest["m1_contract"]["test_records"] = 1

    with pytest.raises(RuntimeError, match="M1 split-size mismatch"):
        bootstrap_models._validate_manifest(manifest, "models-v1")
