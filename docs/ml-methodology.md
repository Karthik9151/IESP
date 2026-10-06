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

The full acceptance runner also records the fitted vocabulary size and feature
matrix shapes and verifies that validation/test transformation leaves both the
vocabulary and IDF state unchanged.

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
- models/phishing/m2_acceptance.json

The metadata includes the artifact size and SHA-256 digest so an externally
generated model can be integrity-checked without committing the binary.

### Runners

After Milestone 1 data preparation:

    python scripts/run_phishing_model.py

For full acceptance directly from the authoritative MeAJOR file:

    python scripts/run_m2_acceptance.py       --input meajor_cleaned_preprocessed.parquet.gzip

The full acceptance runner applies the same accepted M1 preparation code,
enforces the accepted project fingerprint and split counts, trains on train
only, evaluates validation/test separately, performs the deterministic
retraining check as part of acceptance, and writes JSON evidence.

No sampling or artificial row cap is applied.

### Real-data acceptance status

The implementation is complete, but full research acceptance still requires
executing the new runner against the exact authoritative Parquet and retaining
the resulting metrics/artifact evidence.

The accepted M1 project fingerprint is:

34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

No real-data performance number is claimed until that execution occurs.

No historical performance number is treated as a reproduced M2 result.
