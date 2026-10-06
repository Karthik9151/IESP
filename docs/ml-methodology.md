# IESP Machine-Learning Methodology

## Milestone 2 — Phishing baseline

Milestone 2 implements the academic phishing classifier as a reproducible,
leakage-safe TF-IDF + LinearSVC baseline.

### Model contract

- Input: text_normalized
- Target: label
- Label 0: benign
- Label 1: phishing
- Positive class: phishing (1)
- Training: 70% of the accepted Milestone 1 dataset
- Validation: 15%, used for diagnostics/model checking
- Test: 15%, held out for final evaluation
- Split seed: 42
- Features: TF-IDF word unigrams + bigrams
- Classifier: scikit-learn LinearSVC
- C: 1.0
- Maximum iterations: 5000
- Random state: 42

### Leakage boundary

The sklearn Pipeline contains TfidfVectorizer followed by LinearSVC.
The pipeline is fitted only on the training split. Therefore the TF-IDF
vocabulary and IDF statistics cannot use validation or test text.

Validation and test data are transformed by the already-fitted pipeline.
No TF-IDF fitting occurs on those splits.

Unit tests verify that transforming validation text does not change the
fitted vocabulary.

### Evaluation

The evaluator reports Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC,
a 2x2 confusion matrix, and TN/FP/FN/TP. Phishing is the positive class.

ROC-AUC and PR-AUC use the raw LinearSVC decision_function margin. This is a
ranking score, NOT a probability. LinearSVC does not expose predict_proba.
Probability semantics can be added later only through an explicit calibration
stage if the product requires them.

### Validation versus test

Validation results are diagnostics for model checking and configuration
decisions. The test set is the final held-out evaluation and must not be used
for tuning.

### Artifact policy

Generated artifacts remain ignored by Git:

- models/phishing/phishing_pipeline.joblib
- models/phishing/metadata.json

The repository versions model code and configuration rather than large binary
model artifacts.

### Reproducible runner

After Milestone 1 data preparation:

    python scripts/run_phishing_model.py

Optional paths:

    python scripts/run_phishing_model.py \
      --train data/processed/train.parquet \
      --validation data/processed/validation.parquet \
      --test data/processed/test.parquet \
      --metrics-output /tmp/iesp-phishing-metrics.json

### Real-data acceptance status

The M2 implementation is present on v0.3. However, the authoritative MeAJOR
Parquet is not stored in the repository and is not available as a usable local
copy in the current environment. Therefore no real-data performance metrics
are claimed.

Full M2 acceptance requires:
1. Reproduce the accepted M1 project fingerprint exactly.
2. Train on the M1 train split only.
3. Record validation metrics separately.
4. Record final held-out test metrics.
5. Confirm deterministic rerun behavior.
6. Confirm artifact save/load reproduces predictions.

No historical performance number is treated as a reproduced M2 result.
