# IESP Implementation Plan

This is the staged implementation contract for the Intelligent Email Security & Prioritization System.

## Milestone 0 — Architecture

**Objective:** Audit the repository and establish a security-first architecture before implementation.

**Status:** Complete.

**Expected commit:** milestone-0: establish repository audit and architecture

---

## Milestone 1 — Dataset Pipeline

**Objective:** Obtain and reproducibly prepare the authoritative dataset.

**Status:** **COMPLETE**

**Implemented files:**

- src/ml/data/pipeline.py
- configs/dataset.yaml
- scripts/run_dataset_pipeline.py
- tests/test_dataset_pipeline.py
- docs/dataset.md
- docs/milestone1-acceptance-report.md
- requirements-ml.txt

**Verified acceptance:**

- authoritative MeAJOR source identified;
- schema verified;
- missing label/body records handled;
- labels restricted to 0/1;
- exact full-record duplicates removed;
- text_raw preserved;
- conservative text_normalized created;
- 70/15/15 stratified split created with random state 42;
- exact fingerprint leakage checked across splits;
- split reproducibility verified;
- final dataset fingerprint and split fingerprints recorded;
- TF-IDF was not fitted before the split.

**Verified final counts:** 108,670 unique records: 60,636 benign and 48,034 phishing.

**Expected commit:** milestone-1: build reproducible dataset pipeline

---

## Milestone 2 — Phishing ML

**Objective:** Implement the academic TF-IDF + SVM phishing baseline.

**Status:** **IMPLEMENTED ON v0.3; REAL-DATA ACCEPTANCE PENDING**

Implemented:
- text_normalized input;
- TF-IDF word unigrams and bigrams;
- training-only TF-IDF fitting through an sklearn Pipeline;
- LinearSVC phishing classifier;
- deterministic configuration;
- prediction labels and raw decision scores;
- validation and held-out test evaluation;
- Accuracy, Precision, Recall, F1, ROC-AUC and PR-AUC;
- 2x2 confusion matrix and TP/TN/FP/FN;
- model persistence support;
- leakage, dimensions, deterministic inference, persistence and evaluation tests;
- M1 fingerprint and split-count gate in the real-data runner;
- methodology and acceptance documentation.

**Files:** src/ml/phishing/, models/phishing/, configs/phishing.yaml, tests/test_phishing_model.py, scripts/run_phishing_model.py, docs/ml-methodology.md, docs/milestone2-acceptance-report.md.

**Acceptance boundary:** code and fixture tests are implemented. Full acceptance requires the exact accepted M1 fingerprint, train/validation/test counts, real-data training, held-out metrics, deterministic rerun, and artifact save/load verification. No real-data metrics are claimed yet.

**Expected commit:** milestone-2: implement phishing ML baseline

---

## Milestone 3 — Priority ML

**Objective:** Build the VADER + engineered features + Logistic Regression priority baseline for eligible non-phishing mail.

**Tasks:** define proxy labels; feature extraction; VADER; Logistic Regression; P1/P2/P3 evaluation; limitations.

**Files:** src/ml/priority/, models/priority/, configs/priority.yaml, tests/test_priority_model.py.

**Dependencies:** Milestones 1–2; VADER; scikit-learn.

**Tests:** feature extraction, labels, inference, held-out evaluation, regression.

**Acceptance:** priority model is separate from security classification; proxy labels are not presented as human judgment.

**Expected commit:** milestone-3: implement priority ML baseline

---

## Milestone 4 — Security Engine

**Objective:** Build the enhanced security analysis and decision layer around the academic baseline.

**Tasks:** safe MIME/header parsing; security indicators; URL/attachment metadata analysis; deterministic rules; combine ML evidence and security signals; controlled outcomes: PHISHING, SUSPICIOUS, NON-PHISHING, REVIEW REQUIRED.

**Files:** src/security/, src/parsing/, src/domain/, configs/security.yaml, tests/security/, docs/threat-model.md.

**Dependencies:** Milestones 1–3.

**Tests:** malformed MIME/header, URL/SSRF, attachment safety, rules, decision boundaries.

**Acceptance:** security classification happens before priority; no attachment execution; no automatic URL visits; SSRF protections; safe logging.

**Expected commit:** milestone-4: add security analysis and decision engine

---

## Milestone 5 — FastAPI Backend

**Objective:** Expose the analysis system through a validated API.

**Tasks:** FastAPI app; schemas; analysis endpoint; health/readiness; validation; safe errors/logging; persistence service abstraction; authentication/authorization as required.

**Files:** backend/app/, backend/tests/, backend dependency manifest, configs/.

**Dependencies:** Milestones 1–4.

**Tests:** unit, API contract, negative-input, auth/security regression tests.

**Acceptance:** secure API contract without secret or unnecessary body leakage.

**Expected commit:** milestone-5: add secure FastAPI backend

---

## Milestone 6 — React Dashboard

**Objective:** Provide a safe interface for security and priority results.

**Tasks:** React/Vite app; inbox/results; message detail; security signals; review queue; priority display only when eligible; API client; safe email rendering.

**Files:** frontend/, frontend/src/, frontend/tests/.

**Dependencies:** Milestone 5; Node.js/npm.

**Tests:** component, API integration, sanitization, accessibility.

**Acceptance:** security result is clearly separate from priority; untrusted email content is safely rendered.

**Expected commit:** milestone-6: add React security dashboard

---

## Milestone 7 — Email Integrations

**Objective:** Connect providers through one provider-neutral abstraction.

**Tasks:** define MailProvider interface; Gmail API adapter; Microsoft Graph adapter; IMAP adapter where required; OAuth/token lifecycle; least-privilege scopes; normalization; timeout/retry/rate-limit handling.

**Files:** src/integrations/mail/, provider adapters, tests/integrations/, docs/mail-integrations.md.

**Dependencies:** Milestone 5; provider APIs/SDKs.

**Tests:** adapter contracts, mocked providers, token handling, failures/retries, controlled provider integration tests.

**Acceptance:** interchangeable adapters; no stored passwords; secrets outside source control.

**Expected commit:** milestone-7: add mail-provider abstraction and integrations

---

## Milestone 8 — Docker + DevSecOps

**Objective:** Containerize the system and automate quality/security checks.

**Tasks:** Docker; local orchestration where useful; lint/format/type checks; tests; dependency scanning; secret scanning; pinned/locked dependencies.

**Files:** Dockerfile, orchestration config, .dockerignore, .github/workflows/, lockfiles, docs/deployment.md.

**Dependencies:** Milestones 5–7.

**Tests:** image build, smoke tests, CI, vulnerability scan, secret scan.

**Acceptance:** reproducible build and clean/triaged CI security checks.

**Expected commit:** milestone-8: containerize and add DevSecOps CI

---

## Milestone 9 — Security/Integration Testing

**Objective:** Validate the complete system against functional and security requirements.

**Tasks:** end-to-end tests; malformed/adversarial input; SSRF; attachment safety; auth; rate limits; provider integration; ML regression; false-positive/false-negative review; residual-risk documentation.

**Files:** tests/e2e/, tests/security/, tests/integration/, docs/test-report.md.

**Dependencies:** Milestones 1–8.

**Tests:** full automated suite plus controlled manual security testing.

**Acceptance:** critical issues resolved or explicitly release-blocked; regression suite passes; limitations documented.

**Expected commit:** milestone-9: complete security and integration validation

---

## Milestone 10 — Deployment

**Objective:** Deploy the validated system to a controlled production environment.

**Tasks:** hosting choice; external secret management; database/network/TLS configuration; deployment; monitoring; backups; rollback; least-privilege production mail credentials; smoke tests.

**Files:** infra/ or provider-specific deployment config; docs/deployment.md; docs/operations.md.

**Dependencies:** Milestones 1–9.

**Tests:** production smoke, health, auth, mail integration, rollback.

**Acceptance:** reproducible deployment with TLS, managed secrets, access controls, monitoring and rollback.

**Expected commit:** milestone-10: deploy validated IESP system

## Global execution order

```text
Ingestion
  ↓
Safe MIME/header parsing
  ↓
Security feature analysis + phishing evidence
  ↓
Security decision
  ↓
PHISHING / SUSPICIOUS / NON-PHISHING / REVIEW REQUIRED
  ↓
Priority classification only for eligible non-phishing messages
  ↓
P1 / P2 / P3
  ↓
FastAPI
  ↓
React
  ↓
Mail integrations
  ↓
DevSecOps
  ↓
Security/integration testing
  ↓
Deployment
```

The academic ML baselines remain separately measurable from the enhanced security engine.

Milestone 2 may begin only after the Milestone 1 repository implementation has been locally verified against the authoritative dataset.


## Actual implementation status — 2026-10-06

M2: IMPLEMENTED; real-data acceptance PENDING until the accepted MeAJOR dataset is available for fingerprint and held-out validation.

M3: IMPLEMENTED. Priority uses VADER + transparent engineered features + Logistic Regression with deterministic proxy/project labels P1/P2/P3. Proxy labels are not human annotations.

M4: IMPLEMENTED. Safe MIME/header parsing, URL structural analysis, metadata-only attachment analysis, configurable security decision matrix, REVIEW REQUIRED fail-safe path, explicit priority gating and safe logging are present.

M5: IMPLEMENTED. FastAPI provides /api/v1/analyze, /health and /ready with strict Pydantic schemas, environment-provided API-key authentication, authorization boundary, request IDs, restrictive CORS, safe errors and persistence abstraction.

M6–M10 remain future milestones.
