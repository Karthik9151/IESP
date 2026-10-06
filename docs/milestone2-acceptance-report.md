# Milestone 2 Acceptance Report

Canonical project state: development  
Date: 2026-10-07

## Implementation status

M2 is implemented in the consolidated project state. Its phishing pipeline includes the acceptance hardening added during the v0.3 development branch. The runner now performs a deterministic second-training/inference check and reloads the saved artifact to verify prediction equivalence.

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
| Artifact persistence, SHA-256 metadata, and reload equivalence | Implemented |
| Real MeAJOR training run | BLOCKED: source Parquet unavailable |
| Real held-out metrics | NOT CLAIMED |
| Exact accepted M1 fingerprint re-verification here | BLOCKED |

## Acceptance boundary

M2 is implemented but not fully research-accepted until the exact accepted M1 dataset is available and the fingerprint, split counts, real training, validation/test metrics, deterministic rerun and artifact save/load evidence are produced. No real-data metric is fabricated.

Accepted M1 project fingerprint:
34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

Accepted splits: train 76,069; validation 16,300; test 16,301.


## Project milestone state

- **M0 — Foundation:** repository structure, configuration, documentation, and baseline architecture.
- **M1 — Dataset foundation:** MeAJOR validation, normalization, exact deduplication, deterministic stratified split, leakage/integrity checks, reproducibility, and acceptance documentation.
- **M2 — Phishing ML:** TF-IDF + LinearSVC, leakage-safe training boundary, evaluation, prediction API, deterministic retraining, artifact integrity, and authoritative-data acceptance runner. Real-data acceptance is still pending.
- **M3 — Priority ML:** VADER + engineered urgency features + Logistic Regression with deterministic P1/P2/P3 proxy labels; metrics are proxy-policy agreement, not human urgency accuracy.
- **M4 — Security engine:** safe email parsing, header/URL/attachment analysis, fail-closed decisions, explicit priority eligibility, and secret-safe logging.
- **M5 — API layer:** versioned FastAPI analyze endpoint, health/readiness, strict schemas, API-key authentication/authorization boundary, request IDs, restrictive CORS, safe errors, and persistence abstraction.

Branches are development history, not milestones. `v0.2` is identical to the original `main` state; `v0.3` was an intermediate M2 implementation branch; `development` is the consolidated implementation branch.
