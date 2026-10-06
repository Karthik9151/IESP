# IESP Implementation Plan

This is the staged implementation contract for the Intelligent Email Security & Prioritization System.

## Milestone 0 — Architecture

**Status:** Complete.

## Milestone 1 — Dataset Pipeline

**Status:** **COMPLETE**

The authoritative MeAJOR source was prepared with schema validation, exact
full-record deduplication, conservative text normalization, deterministic
70/15/15 stratified splitting, fingerprint leakage checks, and reproducibility
evidence.

## Milestone 2 — Phishing ML

**Objective:** Implement the academic TF-IDF + SVM phishing baseline.

**Status:** **IMPLEMENTED ON v0.3; REAL-DATA ACCEPTANCE PENDING**

Implemented:
- text_normalized as the model input;
- TF-IDF word unigrams and bigrams;
- TF-IDF fitted only through the training pipeline;
- LinearSVC phishing classifier;
- deterministic configuration;
- prediction labels and raw decision scores;
- validation and final held-out test evaluation;
- Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC;
- 2x2 confusion matrix and TP/TN/FP/FN;
- model save/load support;
- small fixture tests for leakage, dimensions, inference, determinism,
  persistence, and evaluation;
- M2 methodology and acceptance documentation.

Files:
- src/ml/phishing/
- configs/phishing.yaml
- scripts/run_phishing_model.py
- tests/test_phishing_model.py
- docs/ml-methodology.md
- docs/milestone2-acceptance-report.md

Important: LinearSVC decision_function output is a margin/ranking score, not a
probability. Calibration is intentionally deferred because probability
semantics are not currently required.

Full acceptance is pending execution against the exact accepted M1 dataset.
No real-data performance metric is claimed until that execution is completed.

**Expected final commit:** milestone-2: implement phishing ML baseline

## Milestone 3 — Priority ML

**Objective:** Build the VADER + engineered features + Logistic Regression priority baseline for eligible non-phishing mail.

**Status:** Not started.

## Milestone 4 — Security Engine

**Status:** Not started.

## Milestone 5 — FastAPI Backend

**Status:** Not started.

## Milestone 6 — React Dashboard

**Status:** Not started.

## Milestone 7 — Email Integrations

**Status:** Not started.

## Milestone 8 — Docker + DevSecOps

**Status:** Not started.

## Milestone 9 — Security/Integration Testing

**Status:** Not started.

## Milestone 10 — Deployment

**Status:** Not started.

## Global execution order

Ingestion → safe MIME/header parsing → security feature analysis → security
decision → phishing/suspicious/non-phishing/review-required → priority only
for eligible non-phishing → P1/P2/P3 → FastAPI → React → mail integrations →
DevSecOps → security/integration testing → deployment.
