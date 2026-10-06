import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from src.ml.phishing.predict import predict_labels, predict_scores
from src.ml.phishing.train import save_phishing_model, train_phishing_model


def test_save_phishing_model_records_artifact_hash(tmp_path):
    frame = pd.DataFrame(
        {
            "text_normalized": [
                "normal project meeting",
                "urgent verify account",
                "team lunch tomorrow",
                "security alert password",
            ],
            "label": [0, 1, 0, 1],
        }
    )
    config = {
        "text_column": "text_normalized",
        "label_column": "label",
        "features": {"ngram_range": [1, 2], "min_df": 1, "max_df": 1.0},
        "model": {"C": 1.0, "max_iter": 5000, "random_state": 42},
    }

    model = train_phishing_model(frame, config)
    artifact = tmp_path / "phishing_pipeline.joblib"
    artifact_path, metadata_path = save_phishing_model(
        model,
        artifact,
        metadata={"test": True},
    )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    assert artifact_path.exists()
    assert payload["artifact"] == artifact.name
    assert payload["artifact_sha256"] == digest
    assert payload["artifact_size_bytes"] == artifact.stat().st_size

    loaded = joblib.load(artifact_path)
    assert np.array_equal(
        predict_labels(model, frame["text_normalized"]),
        predict_labels(loaded, frame["text_normalized"]),
    )
    assert np.allclose(
        predict_scores(model, frame["text_normalized"]),
        predict_scores(loaded, frame["text_normalized"]),
    )
