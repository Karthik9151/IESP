# Milestone 2 Acceptance Report

Repository state: main  
Date: 2026-10-07

## Implementation status

M2 is implemented and has crossed the real-data acceptance boundary through the authoritative model-release workflow. Its phishing pipeline includes the acceptance hardening added during the v0.3 development branch. The runner performs a deterministic second-training/inference check and reloads the saved artifact to verify prediction equivalence.

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
| Artifact persistence, SHA-256 metadata, and reload equivalence | PASS by release workflow |
| Real MeAJOR training run | PASS — model-release workflow #16 |
| Real held-out metrics | PRODUCED by workflow and published as release assets |
| Exact accepted M1 fingerprint re-verification | PASS — release manifest enforced the accepted fingerprint and split sizes |

## Acceptance evidence

Authoritative model-release workflow **#16** ran from commit `1b84ff5f2a8d33b22cab6294b085d97e8964cb21` and completed successfully.

The workflow:
1. downloaded `meajor_cleaned_preprocessed.parquet.gzip` from Zenodo record `18471483`;
2. verified MD5 `78e397ad8447bcdba5a98097921ba8bd`;
3. ran the accepted M1 dataset pipeline;
4. trained and validated the phishing model;
5. trained the priority model;
6. built the model manifest;
7. checked artifact size limits;
8. published `models-v1`;
9. verified all seven expected release assets and the release manifest.

Accepted M1 dataset fingerprint:

`34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582`

Accepted splits: train 76,069; validation 16,300; test 16,301.

## Acceptance boundary

M2 is accepted for the repository/runtime artifact pipeline based on the successful authoritative-data release execution above. This report does **not** reproduce or invent numeric metric values; the workflow-generated metric JSON files are the evidence artifacts.

## Milestone state

- **M0 — Foundation:** repository structure, configuration, documentation, and baseline architecture.
- **M1 — Dataset foundation:** MeAJOR validation, normalization, exact deduplication, deterministic stratified split, leakage/integrity checks, reproducibility, and acceptance documentation.
- **M2 — Phishing ML:** TF-IDF + LinearSVC, leakage-safe training boundary, evaluation, prediction API, deterministic retraining, artifact integrity, and authoritative-data acceptance.
- **M3 — Priority ML:** VADER + engineered urgency features + Logistic Regression with deterministic P1/P2/P3 proxy labels; metrics are proxy-policy agreement, not human urgency accuracy.
- **M4 — Security engine:** safe email parsing, header/URL/attachment analysis, fail-closed decisions, explicit priority eligibility, and secret-safe logging.
- **M5 — API layer:** versioned FastAPI analyze endpoint, health/readiness, strict schemas, server-side authentication/authorization boundary, request IDs, restrictive CORS, safe errors, and persistence abstraction.

Branches are development history, not milestones. `v0.2` is identical to the original `main` state; `v0.3` was an intermediate M2 implementation branch; `development` is historical consolidated implementation work, while `main` is the current release/reference branch.
