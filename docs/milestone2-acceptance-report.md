# Milestone 2 Acceptance Report

Branch: v0.3  
Date: 2026-10-06

## Implementation status

| Requirement | Status |
|---|---|
| TF-IDF feature construction | PASS |
| TF-IDF fit only on training data | PASS by design + unit test |
| Linear SVM baseline | PASS |
| Deterministic configuration | PASS |
| Prediction API | PASS |
| Decision-score semantics | PASS |
| Accuracy/Precision/Recall/F1 | PASS |
| ROC-AUC / PR-AUC | PASS |
| Confusion matrix + TN/FP/FN/TP | PASS |
| Persistence support | PASS |
| Unit tests | Implemented |
| Real MeAJOR training run | BLOCKED: source Parquet unavailable |
| Real held-out metrics | NOT CLAIMED |
| M1 fingerprint re-verification in this environment | BLOCKED |

## Acceptance boundary

This report does not claim that M2 has passed full research acceptance.
The implementation and small fixture tests are present, but full acceptance
requires execution against the exact accepted Milestone 1 dataset.

Accepted M1 project fingerprint:

34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

The raw dataset must not be committed to GitHub.

## Required final evidence

- M1 fingerprint reproduced exactly.
- Train/validation/test counts match the accepted split.
- Model trained on train only.
- Validation metrics recorded separately.
- Test metrics recorded as final held-out results.
- Confusion matrix is 2x2 with phishing as positive class.
- Raw SVM decision scores are never described as probabilities.
- Artifact save/load reproduces predictions.
- No raw dataset or generated model binaries committed.
