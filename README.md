# IESP

## Intelligent Email Security & Prioritization System

IESP is a production-oriented academic prototype combining NLP, machine learning, cybersecurity analysis, and real-time email integration.

### Core decision flow

Email -> Security analysis -> Security decision -> Priority analysis for eligible non-phishing email -> P1/P2/P3

Security evaluation always happens before priority classification.

### Current status

**Milestone 1 — Dataset + ML pipeline foundation: COMPLETE**

The authoritative MeAJOR dataset was verified, structurally prepared, exactly
deduplicated, validated, split with stratification, checked for cross-split
exact leakage, and documented.

**Milestone 2 — Phishing ML: IMPLEMENTED; REAL-DATA ACCEPTANCE PENDING**

Branch v0.3 contains a leakage-safe TF-IDF + LinearSVC phishing baseline,
prediction/evaluation utilities, tests, configuration, and a real-data runner.
The authoritative Parquet is not committed to GitHub, so final performance
metrics must be produced in a controlled local/Colab environment.

Backend, frontend, enhanced security engine, mail integrations, CI/CD, and deployment remain deferred.

### Milestone 2 implementation

- src/ml/phishing/features.py — TF-IDF construction and schema validation.
- src/ml/phishing/train.py — TF-IDF + LinearSVC training and artifact persistence.
- src/ml/phishing/predict.py — labels and raw SVM decision scores.
- src/ml/phishing/evaluate.py — required classification metrics and confusion matrix.
- configs/phishing.yaml — reproducible feature/model/evaluation configuration.
- scripts/run_phishing_model.py — trains on M1 train and evaluates validation/test.
- tests/test_phishing_model.py — leakage, dimensions, determinism, persistence and evaluation tests.
- docs/ml-methodology.md — methodology and score semantics.
- docs/milestone2-acceptance-report.md — acceptance boundary and required evidence.

The LinearSVC decision_function output is a ranking margin, **not a probability**.

The authoritative dataset and generated model artifacts are not committed to GitHub.

### Research integrity

The project does not reuse historical model metrics as reproduced results
unless the exact dataset, preprocessing, split, parameters, and evaluation
procedure are matched.


### Milestone 3–5 implementation

Milestone 3 adds the VADER + engineered-feature + Logistic Regression priority baseline with deterministic P1/P2/P3 proxy labels. These labels are project/proxy labels, not human urgency annotations.

Milestone 4 adds provider-neutral domain models, safe MIME/header parsing, structural URL analysis without network requests, metadata-only attachment policy, configurable fail-closed security decisions, explicit priority eligibility, and secret-safe logging.

Milestone 5 adds the versioned FastAPI API at /api/v1/analyze, public /health, readiness /ready, strict Pydantic validation, environment-provided API-key authentication, an authorization boundary, request IDs, restrictive CORS, safe errors, and a persistence abstraction.

Security invariant: Untrusted email -> safe parsing -> security analysis -> security decision -> priority only for eligible NON-PHISHING email -> P1/P2/P3.
