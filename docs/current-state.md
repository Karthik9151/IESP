# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** Karthik9151/IESP  
**Default branch:** main  
**Milestone status:** M0–M5 implementation consolidated; M2 real-data acceptance pending

## Repository inventory

The repository contains the project foundation plus the implemented M1–M5 layers. The M2 authoritative dataset run remains an external acceptance step.

.
├── README.md
├── .env.example
├── .gitignore
├── requirements-ml.txt
├── .github/
│   └── workflows/
│       └── .gitkeep
├── app/
│   └── .gitkeep
├── configs/
│   └── dataset.yaml
├── data/
│   └── .gitkeep
├── docs/
│   ├── architecture.md
│   ├── current-state.md
│   ├── dataset.md
│   ├── deployment.md
│   ├── implementation-plan.md
│   ├── limitations.md
│   ├── mail-integrations.md
│   ├── milestone1-acceptance-report.md
│   ├── ml-methodology.md
│   └── threat-model.md
├── frontend/
│   └── .gitkeep
├── models/
│   └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── scripts/
│   ├── run_dataset_pipeline.py
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   └── ml/
│       ├── __init__.py
│       └── data/
│           ├── __init__.py
│           └── pipeline.py
└── tests/
    ├── test_dataset_pipeline.py
    └── .gitkeep

## Functionality status

| Area | Current state |
|---|---|
| Milestone 1 dataset preparation | Implemented |
| Dataset provenance/documentation | Implemented |
| Exact full-record deduplication | Implemented |
| Text normalization | Implemented |
| Stratified train/validation/test split | Implemented |
| Split leakage/integrity checks | Implemented |
| Dataset manifest generation | Implemented |
| FastAPI backend | Implemented (M5) |
| React/Vite frontend | Not implemented |
| Phishing SVM | Implemented on v0.3; real-data acceptance pending |
| Priority Logistic Regression | Implemented (M3) |
| Enhanced security engine | Implemented (M4) |
| Gmail integration | Not implemented |
| Microsoft Graph integration | Not implemented |
| Generic IMAP integration | Not implemented |
| Database | Not implemented |
| Docker | Not implemented |
| GitHub Actions CI | Placeholder only |
| Model artifacts | Not committed; generated locally by M2 runner |

## Milestone 1 verified dataset

The accepted Colab audit verified:

- Raw records: 108,685
- Usable labeled-text records: 108,683
- Exact duplicate copies: 13
- Final unique records: 108,670
- Benign: 60,636
- Phishing: 48,034
- Train: 76,069
- Validation: 16,300
- Test: 16,301
- Random state: 42
- Stratification: label
- Project fingerprint: 34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

See docs/dataset.md and docs/milestone1-acceptance-report.md for the complete acceptance record.

## Data storage policy

The authoritative MeAJOR Parquet file is not stored in the repository. The repository .gitignore excludes raw and processed data. The pipeline reads the source file from a local or Colab path and writes generated Parquet outputs under data/processed/.

## Research and security constraints

1. Email content remains untrusted data.
2. No attachment execution or automatic URL visits are implemented here.
3. TF-IDF has not been fitted in Milestone 1.
4. Model preprocessing belongs after the split and must be fitted only on training data.
5. Historical performance claims are not considered reproduced results.

Milestones M0–M5 are implemented in the consolidated development state. M2 real-data acceptance remains pending because the authoritative Parquet is not available in this environment. M3 uses deterministic proxy priority labels; M4 security controls are regression-tested; M5 exposes the versioned FastAPI application layer.


## Post-M5 implementation update — 2026-10-06

| Milestone | Implementation | Acceptance boundary |
|---|---|---|
| M2 Phishing ML | Implemented with TF-IDF + LinearSVC, runtime feature-state audit, deterministic retraining, and artifact integrity checks | Real-data acceptance PENDING because the authoritative Parquet is unavailable here |
| M3 Priority ML | Implemented with VADER, engineered urgency features, proxy labels, and Logistic Regression | Fixture/code verification implemented; real model execution requires the pinned VADER dependency |
| M4 Security Engine | Implemented with safe parsing, URL/attachment analysis, fail-closed decisioning, explicit priority gating, and safe logging | Security regression tests implemented |
| M5 FastAPI | Implemented with versioned analyze endpoint, health/readiness, strict schemas, API-key auth, authorization, safe errors, request IDs, restrictive CORS, and repository abstraction | API regression tests implemented |

Security classification always precedes priority classification. Priority is requested only after an explicit NON-PHISHING decision. Raw email bodies, attachments, URLs and secrets are not exposed through logs or API responses by default.
