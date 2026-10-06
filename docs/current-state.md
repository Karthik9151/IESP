# Current Repository State

Audit date: 2026-10-06  
Repository: Karthik9151/IESP  
Default branch: main  
Branch under development: v0.3  
Milestone status: Milestone 2 code implemented; real-data acceptance pending

## Repository inventory

The repository contains the Milestone 0 foundation, Milestone 1 dataset
pipeline, and the Milestone 2 phishing baseline.

### Milestone 2 files

- src/ml/phishing/__init__.py
- src/ml/phishing/features.py
- src/ml/phishing/train.py
- src/ml/phishing/predict.py
- src/ml/phishing/evaluate.py
- configs/phishing.yaml
- scripts/run_phishing_model.py
- tests/test_phishing_model.py
- docs/ml-methodology.md
- docs/milestone2-acceptance-report.md

## Functionality status

| Area | Current state |
|---|---|
| Milestone 1 dataset preparation | Implemented and previously accepted |
| Phishing TF-IDF features | Implemented |
| Phishing LinearSVC baseline | Implemented |
| Validation/test evaluation | Implemented |
| Model persistence | Implemented; artifacts remain ignored |
| Real-data M2 execution | Pending authoritative Parquet availability |
| FastAPI backend | Not implemented |
| React/Vite frontend | Not implemented |
| Priority Logistic Regression | Not implemented |
| Enhanced security engine | Not implemented |
| Gmail / Graph / IMAP | Not implemented |
| Docker / DevSecOps | Not implemented |
| Database | Not implemented |

## M1 reference

Accepted M1 project fingerprint:

34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582

Accepted split counts:
- train: 76,069
- validation: 16,300
- test: 16,301

M2 does not alter the M1 data pipeline.

## Data and artifact policy

The authoritative MeAJOR Parquet is not committed to GitHub.
Generated processed data and model binaries remain ignored by .gitignore.

## Acceptance boundary

M2 implementation is complete on this branch, but full milestone acceptance
is pending real-data execution. No fabricated performance metrics are recorded.
