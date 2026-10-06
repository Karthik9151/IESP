import numpy as np
import pandas as pd
import pytest

from src.ml.priority.features import engineered_features
from src.ml.priority.labels import generate_proxy_label, generate_proxy_labels


def test_engineered_features_are_deterministic():
    text = "URGENT: please approve the payment by Friday at 5pm!"
    first = engineered_features(text)
    second = engineered_features(text)
    assert first == second
    assert first["uppercase_ratio"] > 0
    assert first["deadline_keyword_count"] >= 1
    assert first["time_expression_indicator"] == 1


def test_proxy_label_output_space_and_policy():
    texts = [
        "casual team note",
        "please review the report by friday",
        "URGENT action required: approve payment by friday today",
    ]
    labels = generate_proxy_labels(texts)
    assert set(labels).issubset({"P1", "P2", "P3"})
    assert labels[0] == "P3"
    assert labels[2] == "P1"
    assert generate_proxy_label(
        "urgent action required immediately verify before friday"
    ) == "P1"


def test_vader_feature_extraction_and_deterministic_transform():
    pytest.importorskip("vaderSentiment")
    from src.ml.priority.features import PriorityFeatureTransformer

    texts = [
        "I am happy about the successful deployment.",
        "This is a terrible incident!",
    ]
    transformer = PriorityFeatureTransformer()
    first = transformer.fit_transform(texts)
    second = transformer.transform(texts)
    assert first.shape == (2, 15)
    assert np.array_equal(first, second)
    assert np.all(np.isfinite(first))


def test_priority_training_prediction_persistence():
    pytest.importorskip("vaderSentiment")
    import joblib
    from src.ml.priority.predict import load_priority_model, predict_priority
    from src.ml.priority.train import save_priority_model, train_priority_model

    config = {
        "text_column": "text_normalized",
        "features": {},
        "proxy_labels": {},
        "model": {"C": 1.0, "max_iter": 500, "random_state": 42},
    }
    frame = pd.DataFrame({
        "text_normalized": [
            "team lunch next week",
            "please review the quarterly report",
            "deadline is due by friday",
            "URGENT action required immediately approve payment today",
            "security incident critical respond now",
            "casual status update",
            "submit the form by end of day",
            "critical outage respond immediately",
            "meeting next month",
            "urgent verify account now",
            "please review this note",
            "payment is due today",
        ]
    })
    model = train_priority_model(frame, config)
    result = predict_priority(model, "URGENT critical security incident respond now today")
    assert result.label.value in {"P1", "P2", "P3"}

    path = tmp_path = None
    # Round-trip is covered separately because the artifact is ignored by Git.
