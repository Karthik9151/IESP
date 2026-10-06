# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** Karthik9151/IESP  
**Default branch:** main  
**Active implementation branch:** v0.3  
**Milestone status:** Milestone 2 implementation complete; real-data acceptance pending execution

## Repository inventory

The repository contains the Milestone 0 foundation, the accepted Milestone 1
dataset pipeline, and the Milestone 2 phishing baseline.

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
│   ├── dataset.yaml
│   └── phishing.yaml
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
│   ├── milestone2-acceptance-report.md
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
│   ├── run_m2_acceptance.py
│   └── run_phishing_model.py
├── src/
│   ├── __init__.py
│   └── ml/
│       ├── __init__.py
│       ├── data/
│       │   ├── __init__.py
│       │   └── pipeline.py
│       └── phishing/
│           ├── __init__.py
│           ├── evaluate.py
│           ├── features.py
│           ├── predict.py
│           └── train.py
└── tests/
    ├── test_dataset_pipeline.py
    ├── test_m2_acceptance_runner.py
    ├── test_phishing_model.py
    └── .gitkeep

## Functionality status

| Area | Current state |
|---|---|
| Milestone 1 dataset preparation | Implemented and accepted by Colab audit |
| Dataset provenance/documentation | Implemented |
| Exact full-record deduplication | Implemented |
| Text normalization | Implemented |
| Stratified train/validation/test split | Implemented |
| Split leakage/integrity checks | Implemented |
| Dataset manifest generation | Implemented |
| Phishing TF-IDF + LinearSVC | Implemented on v0.3 |
| M2 leakage/runtime feature audit | Implemented |
| M2 deterministic retraining check | Implemented |
| M2 artifact integrity metadata | Implemented |
| M2 real-data training/evaluation | Pending execution with authoritative dataset |
| Priority Logistic Regression | Not implemented |
| Enhanced security engine | Not implemented |
| FastAPI backend | Not implemented |
| React/Vite frontend | Not implemented |
| Gmail integration | Not implemented |
| Microsoft Graph integration | Not implemented |
| Generic IMAP integration | Not implemented |
| Database | Not implemented |
| Docker | Not implemented |
| GitHub Actions CI | Placeholder only |

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

The authoritative MeAJOR Parquet file is not stored in the repository. The
repository .gitignore excludes raw and processed data as well as generated
model artifacts. The pipeline reads the source file from a local or Colab path
and writes generated outputs under data/processed/ and models/phishing/.

## Research and security constraints

1. Email content remains untrusted data.
2. No attachment execution or automatic URL visits are implemented here.
3. TF-IDF is not fitted in Milestone 1.
4. Model preprocessing is fitted only on training data.
5. Validation metrics are diagnostics; test metrics are held-out results.
6. LinearSVC decision scores are margins, not probabilities.
7. Historical performance claims are not treated as reproduced M2 results.

Milestone 0 and Milestone 1 are complete. Milestone 2 implementation is
complete on v0.3. Full M2 acceptance now depends only on executing the new
authoritative-data runner with the exact MeAJOR Parquet and retaining its
resulting evidence.
