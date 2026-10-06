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
prediction/evaluation utilities, tests, configuration, and both a split-based
runner and a one-command authoritative-data acceptance runner.

The authoritative Parquet is not committed to GitHub. Real-data metrics and
the generated model artifact must be produced in Colab or another controlled
environment that has the exact MeAJOR file.

Backend, frontend, enhanced security engine, mail integrations, CI/CD, and deployment remain deferred.

### Milestone 2 implementation

- src/ml/phishing/features.py — TF-IDF construction and schema validation.
- src/ml/phishing/train.py — TF-IDF + LinearSVC training and integrity-verifiable artifact persistence.
- src/ml/phishing/predict.py — labels and raw SVM decision scores.
- src/ml/phishing/evaluate.py — required classification metrics and confusion matrix.
- configs/phishing.yaml — reproducible feature/model/evaluation configuration.
- scripts/run_phishing_model.py — trains on accepted M1 splits and evaluates validation/test.
- scripts/run_m2_acceptance.py — runs M1 preparation, verifies the accepted fingerprint/count gate, performs full M2 training/evaluation, checks TF-IDF state stability, deterministic retraining, and writes acceptance evidence.
- tests/test_phishing_model.py — leakage, dimensions, determinism, persistence and evaluation tests.
- tests/test_m2_acceptance_runner.py — artifact hash and save/load regression test.
- docs/ml-methodology.md — methodology and score semantics.
- docs/milestone2-acceptance-report.md — acceptance boundary and required evidence.

The LinearSVC decision_function output is a ranking margin, **not a probability**.

The authoritative dataset and generated model artifacts are not committed to GitHub.

### Real-data acceptance command

From the repository root, with the authoritative file available locally or in Colab:

    python scripts/run_m2_acceptance.py       --input meajor_cleaned_preprocessed.parquet.gzip

The command applies the accepted M1 preprocessing/split, refuses to train if
the M1 fingerprint or split sizes differ, trains without artificial row limits,
evaluates validation and test separately, checks deterministic retraining, and
writes the model artifact plus JSON acceptance evidence under the configured
ignored output paths.

### Research integrity

The project does not reuse historical model metrics as reproduced results
unless the exact dataset, preprocessing, split, parameters, and evaluation
procedure are matched.
