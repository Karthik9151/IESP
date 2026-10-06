# Milestone 2 Acceptance Report

Branch: v0.3  
Date: 2026-10-06

## Implementation status

| Requirement | Status |
|---|---|
| TF-IDF feature construction | PASS |
| TF-IDF fit only on training data | PASS by design + unit tests + runtime audit |
| Linear SVM baseline | PASS |
| Deterministic configuration | PASS |
| Prediction API | PASS |
| Decision-score semantics | PASS |
| Accuracy/Precision/Recall/F1 | PASS |
| ROC-AUC / PR-AUC | PASS |
| Confusion matrix + TN/FP/FN/TP | PASS |
| Persistence support | PASS |
| Artifact integrity metadata | PASS |
| Unit tests | Implemented |
| Full authoritative-data runner | IMPLEMENTED |
| Real MeAJOR training run | PENDING: must be executed with the authoritative Parquet |
| Real held-out metrics | NOT CLAIMED |
| M1 fingerprint re-verification here | NOT EXECUTED: dataset file is not available in this runtime |

## Acceptance boundary

The repository implementation is complete for the M2 contract. Full research
acceptance is intentionally gated on executing the implementation against the
exact accepted Milestone 1 dataset.

Accepted M1 project fingerprint:

34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

Accepted split sizes:

- Train: 76,069
- Validation: 16,300
- Test: 16,301

The raw dataset and generated model binary must not be committed to GitHub.

## What the new acceptance runner verifies

1. Re-applies the repository Milestone 1 preparation and deterministic split.
2. Refuses training if the accepted dataset fingerprint differs.
3. Refuses training if the accepted split sizes differ.
4. Fits TF-IDF + LinearSVC using the train split only.
5. Transforms train, validation, and test with the already-fitted vectorizer.
6. Verifies the TF-IDF vocabulary and IDF state do not change during validation/test transformation.
7. Records validation and held-out test metrics separately.
8. Checks deterministic retraining by default.
9. Saves the model plus metadata containing an artifact SHA-256 digest.
10. Writes machine-readable acceptance evidence to models/phishing/m2_acceptance.json.

No artificial dataset row limit or sampling step is introduced.

## Required final evidence

- M1 fingerprint reproduced exactly.
- Train/validation/test counts match the accepted split.
- Model trained on train only.
- Validation metrics recorded separately.
- Test metrics recorded as final held-out results.
- Confusion matrix is 2x2 with phishing as positive class.
- Raw SVM decision scores are never described as probabilities.
- Artifact save/load reproduces predictions.
- Deterministic retraining check passes.
- No raw dataset or generated model binaries committed.

## Execution

    python scripts/run_m2_acceptance.py       --input meajor_cleaned_preprocessed.parquet.gzip

A successful run prints the acceptance JSON and creates:

- data/processed/meajor_ml.parquet
- data/processed/train.parquet
- data/processed/validation.parquet
- data/processed/test.parquet
- models/phishing/phishing_pipeline.joblib
- models/phishing/metadata.json
- models/phishing/m2_acceptance.json

These generated files remain ignored by Git.
