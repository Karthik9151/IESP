import numpy as np
import pandas as pd
import pytest

from src.ml.phishing.evaluate import evaluate_predictions
from src.ml.phishing.features import build_tfidf_vectorizer, validate_feature_frame
from src.ml.phishing.predict import predict_labels, predict_scores
from src.ml.phishing.train import build_phishing_pipeline, train_phishing_model


def make_frame() -> pd.DataFrame:
    texts = [
        "team meeting agenda for tomorrow",
        "project report attached for review",
        "invoice payment is due next week",
        "security alert verify your account immediately",
        "urgent password reset click the verification link",
        "account suspended confirm credentials now",
        "lunch meeting moved to friday",
        "please review the quarterly report",
        "your payroll statement is available",
        "confirm your mailbox security settings",
        "family dinner this weekend",
        "the deployment completed successfully",
    ]
    labels = [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0]
    return pd.DataFrame({"text_normalized": texts, "label": labels})


def config():
    return {
        "text_column": "text_normalized",
        "label_column": "label",
        "features": {
            "ngram_range": [1, 2],
            "min_df": 1,
            "max_df": 1.0,
            "sublinear_tf": True,
        },
        "model": {"C": 1.0, "max_iter": 5000, "random_state": 42},
    }


def test_tfidf_fit_transform_and_dimensions():
    vectorizer = build_tfidf_vectorizer(config()["features"])
    train = make_frame()["text_normalized"].iloc[:8]
    validation = make_frame()["text_normalized"].iloc[8:]
    train_matrix = vectorizer.fit_transform(train)
    validation_matrix = vectorizer.transform(validation)
    assert train_matrix.shape[0] == 8
    assert validation_matrix.shape[0] == 4
    assert train_matrix.shape[1] == validation_matrix.shape[1]
    assert train_matrix.shape[1] > 0
    assert hasattr(vectorizer, "vocabulary_")
    assert len(vectorizer.vocabulary_) > 0


def test_validation_transform_does_not_change_fitted_vocabulary():
    vectorizer = build_tfidf_vectorizer(config()["features"])
    train = make_frame()["text_normalized"].iloc[:8]
    validation = make_frame()["text_normalized"].iloc[8:]
    vectorizer.fit(train)
    vocabulary_before = dict(vectorizer.vocabulary_)
    vectorizer.transform(validation)
    assert vectorizer.vocabulary_ == vocabulary_before


def test_feature_schema_and_label_validation():
    frame = make_frame()
    validate_feature_frame(frame)
    with pytest.raises(ValueError):
        validate_feature_frame(frame.drop(columns=["text_normalized"]))
    invalid = frame.copy()
    invalid.loc[0, "label"] = 2
    with pytest.raises(ValueError):
        validate_feature_frame(invalid)


def test_training_and_prediction():
    frame = make_frame()
    model = train_phishing_model(frame, config())
    predictions = predict_labels(model, frame["text_normalized"])
    scores = predict_scores(model, frame["text_normalized"])
    assert predictions.shape == (len(frame),)
    assert scores.shape == (len(frame),)
    assert set(predictions).issubset({0, 1})
    assert np.isfinite(scores).all()


def test_deterministic_inference():
    frame = make_frame()
    model_a = train_phishing_model(frame, config())
    model_b = train_phishing_model(frame, config())
    assert np.array_equal(
        predict_labels(model_a, frame["text_normalized"]),
        predict_labels(model_b, frame["text_normalized"]),
    )
    assert np.allclose(
        predict_scores(model_a, frame["text_normalized"]),
        predict_scores(model_b, frame["text_normalized"]),
    )


def test_pipeline_persistence_round_trip(tmp_path):
    frame = make_frame()
    model = train_phishing_model(frame, config())
    path = tmp_path / "phishing_pipeline.joblib"
    import joblib
    joblib.dump(model, path)
    loaded = joblib.load(path)
    assert np.array_equal(
        predict_labels(model, frame["text_normalized"]),
        predict_labels(loaded, frame["text_normalized"]),
    )


def test_evaluation_fields_and_confusion_matrix():
    metrics = evaluate_predictions(
        [0, 0, 1, 1],
        [0, 1, 1, 1],
        [-1.0, 0.2, 0.8, 1.2],
    )
    expected = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
        "confusion_matrix",
        "tn",
        "fp",
        "fn",
        "tp",
        "positive_class",
        "score_semantics",
    }
    assert expected.issubset(metrics)
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]
    assert (metrics["tn"], metrics["fp"], metrics["fn"], metrics["tp"]) == (1, 1, 0, 2)
    assert "not a probability" in metrics["score_semantics"].lower()


def test_pipeline_exposes_tfidf_and_svm():
    pipeline = build_phishing_pipeline(config())
    assert pipeline.named_steps["tfidf"].__class__.__name__ == "TfidfVectorizer"
    assert pipeline.named_steps["svm"].__class__.__name__ == "LinearSVC"


def test_fractional_labels_are_rejected():
    frame = pd.DataFrame({"text_normalized": ["a", "b"], "label": [0.5, 1]})
    with pytest.raises(ValueError):
        train_phishing_model(frame, config())
