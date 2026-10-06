# Milestone 2 Acceptance Report

Branch: development  
Historical snapshot: v0.3  
Date: 2026-10-06

## Implementation status

M2 is implemented on development and preserves the v0.3 baseline. The runner now performs a deterministic second-training/inference check and reloads the saved artifact to verify prediction equivalence.

| Requirement | Status |
|---|---|
| TF-IDF feature construction | PASS by implementation + fixture tests |
| TF-IDF fit only on training data | PASS by sklearn Pipeline + fixture test |
| LinearSVC phishing baseline | PASS |
| Deterministic configuration | PASS |
| Prediction labels and raw decision scores | PASS |
| Accuracy/Precision/Recall/F1 | PASS |
| ROC-AUC/PR-AUC | PASS |
| Confusion matrix + TN/FP/FN/TP | PASS |
| Artifact persistence and reload equivalence | Implemented |
| Real MeAJOR training run | BLOCKED: source Parquet unavailable |
| Real held-out metrics | NOT CLAIMED |
| Exact accepted M1 fingerprint re-verification here | BLOCKED |

## Acceptance boundary

M2 is implemented but not fully research-accepted until the exact accepted M1 dataset is available and the fingerprint, split counts, real training, validation/test metrics, deterministic rerun and artifact save/load evidence are produced. No real-data metric is fabricated.

Accepted M1 project fingerprint:
34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

Accepted splits: train 76,069; validation 16,300; test 16,301.
