# IESP

## Intelligent Email Security & Prioritization System

IESP is a production-oriented academic prototype combining NLP, machine learning, cybersecurity analysis, and real-time email integration.

### Core decision flow

Email -> Security analysis -> Security decision -> Priority analysis for eligible non-phishing email -> P1/P2/P3

Security evaluation always happens before priority classification.

### Current status

**Milestone 1 — Dataset + ML pipeline foundation: COMPLETE**

The authoritative MeAJOR dataset was verified in Google Colab, structurally prepared, exactly deduplicated, validated, split with stratification, checked for cross-split exact leakage, and documented. The repository now contains the reproducible dataset pipeline implementation.

**Milestone 2 — Phishing ML:** not started.

Backend, frontend, enhanced security engine, mail integrations, CI/CD, and deployment remain deferred to their later milestones.

### Milestone 1 implementation

- `src/ml/data/pipeline.py` — structural preparation, normalization, fingerprints, deterministic split and integrity checks.
- `configs/dataset.yaml` — authoritative source, schema, preprocessing, deduplication, split, and output configuration.
- `scripts/run_dataset_pipeline.py` — reproducible pipeline runner.
- `tests/test_dataset_pipeline.py` — dataset pipeline unit tests.
- `docs/dataset.md` — dataset provenance, methodology, verified counts, fingerprints, and leakage policy.
- `docs/milestone1-acceptance-report.md` — final acceptance audit.

The authoritative dataset is **not** committed to GitHub. Raw and generated processed data remain ignored by `.gitignore`.

### Documentation

- `docs/current-state.md`
- `docs/architecture.md`
- `docs/implementation-plan.md`
- `docs/dataset.md`
- `docs/milestone1-acceptance-report.md`
- `docs/threat-model.md`
- `docs/ml-methodology.md`
- `docs/mail-integrations.md`
- `docs/deployment.md`
- `docs/limitations.md`

### Research integrity

The project does not reuse historical model metrics as reproduced results unless the exact dataset, preprocessing, split, parameters, and evaluation procedure are matched.

Milestone 1 verified the authoritative dataset rather than relying on conflicting historical counts.
