# IESP

## Intelligent Email Security & Prioritization System

IESP is a security-first academic prototype that combines deterministic email security analysis, a phishing ML baseline, transparent priority scoring, a FastAPI backend, a React dashboard, and read-only Gmail/Microsoft Graph adapters.

## Security-first decision flow

```text
Email / provider adapter
        ↓
Safe parsing + normalization
        ↓
Security feature extraction
        ↓
TF-IDF + LinearSVC phishing evidence
        ↓
Security decision
        ├── PHISHING
        ├── SUSPICIOUS
        ├── REVIEW REQUIRED
        └── NON-PHISHING
                 ↓
          Priority eligibility
                 ↓
             P1 / P2 / P3
                 ↓
              FastAPI
                 ↓
          React dashboard
```

Priority is never returned for PHISHING, SUSPICIOUS, or REVIEW REQUIRED.

## Repository workflow

`development` is the only active development branch. `main` is the stable/reference branch. Milestones are stages, not branches.

## M0–M8 status

| Milestone | Status | Evidence boundary |
|---|---|---|
| M0 Repository audit + architecture | VERIFIED | Repository structure, architecture, workflow and source-of-truth docs updated |
| M1 Dataset + ML pipeline | VERIFIED | Accepted fingerprint/splits and reproducible pipeline are preserved |
| M2 Security analysis engine / phishing ML | VERIFIED | Authoritative MeAJOR training/validation completed by model-release workflow #16; verified `models-v1` artifacts and manifest published |
| M3 Backend + database | VERIFIED | FastAPI, validation, API-key auth, SQLite metadata persistence, and API regression tests |
| M4 React dashboard | IMPLEMENTED | React/Vite UI, API integration, responsive states, safe text rendering |
| M5 Gmail / Outlook integration | IMPLEMENTED | Read-only provider adapters + OAuth state/PKCE helpers + mocked adapter tests; live provider credentials not tested here |
| M6 Testing + security testing | VERIFIED by CI #47 | Critical backend tests, regression job, dependency audit, frontend tests/build, and secret scan all passed |
| M7 Deployment | IMPLEMENTED / PARTIALLY VERIFIED | Docker, Compose, CI, dependency audit, secret scan; external deployment not executed |
| M8 Documentation + presentation | IMPLEMENTED | Project docs, demo runbook, methodology, threat model, deployment and presentation outline |

## Preserved M1 contract

- Dataset: `meajor_cleaned_preprocessed.parquet.gzip`
- Project fingerprint: `34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582`
- Train: `76069`
- Validation: `16300`
- Test: `16301`
- 70/15/15 stratified split, random state 42
- exact full-record deduplication and cross-split fingerprint leakage checks
- authoritative dataset intentionally excluded from GitHub

## Verified model release

The current model release is `models-v1`. GitHub Actions model-release workflow **#16** completed successfully from commit `1b84ff5f2a8d33b22cab6294b085d97e8964cb21`.

The workflow downloaded the authoritative MeAJOR dataset, verified the accepted M1 checksum/fingerprint/splits, trained both runtime models, published the release assets, and verified the expected release assets and manifest.

## ML baselines

### Phishing
TF-IDF word unigrams/bigrams + LinearSVC. TF-IDF is fitted only on the training split. `decision_function` is a ranking margin, not a probability.

### Priority
VADER sentiment + engineered email urgency features + Logistic Regression. P1/P2/P3 are deterministic proxy/project labels, not human urgency annotations.

## Security controls

Email content is treated only as untrusted data. Attachments are metadata-only and never executed. URLs are inspected structurally and never automatically visited. Local/private IP destinations are escalated as SSRF-sensitive. HTML is analyzed as text and is never rendered by the dashboard. API authentication uses an environment-provided key with constant-time comparison. Logs exclude request bodies, credentials and raw attachments.

## API

- `GET /health`
- `GET /ready`
- `POST /api/v1/analyze`
- `GET /api/v1/stats`
- `GET /api/v1/recent?limit=20`
- `GET /api/v1/analysis/{message_id}`

Analysis requires `X-API-Key` unless authentication is explicitly disabled in development/test mode.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt -r requirements-api.txt
export IESP_ENVIRONMENT=development
export IESP_API_KEY='replace-with-a-long-random-secret'
uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The backend intentionally reports `/ready` as unavailable until required model artifacts exist.

## Reproduce M1 and train models

After obtaining the accepted MeAJOR file locally or in Colab:

```bash
python scripts/run_dataset_pipeline.py --input /path/to/meajor_cleaned_preprocessed.parquet.gzip
python scripts/run_phishing_model.py
python scripts/run_priority_model.py
```

The existing `scripts/run_m2_acceptance.py` refuses to claim acceptance when the fingerprint or split contract does not match.

## Provider integrations

`src/providers/` contains provider-neutral interfaces, Gmail and Microsoft Graph read-only adapters, normalization helpers, and OAuth state/PKCE helpers. No adapter exposes mailbox-mutating operations. Live provider validation requires external application configuration and is not claimed as completed here.

## Research integrity

No accuracy, F1, ROC-AUC, PR-AUC, provider-success, deployment-success, or security-test result is claimed unless that execution was actually observed. External blockers are recorded as PENDING/BLOCKED rather than hidden.
