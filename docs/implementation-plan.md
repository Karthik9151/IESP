# IESP Implementation Plan

This is the staged implementation contract for the Intelligent Email Security & Prioritization System.

## Milestone 0 — Architecture

**Objective:** Audit the repository and establish a security-first architecture before implementation.

**Tasks:** repository audit; component boundaries; academic-vs-enhanced architecture; data flow; security principles; provider abstraction; dataset ambiguity documentation.

**Files:** `docs/current-state.md`, `docs/architecture.md`, `docs/implementation-plan.md`.

**Dependencies:** Git/GitHub only.

**Tests:** audit and documentation consistency review.

**Acceptance:** repository state, architecture, target structure, dataset issue, security requirements and all milestones documented; no implementation started.

**Expected commit:** `milestone-0: establish repository audit and architecture`

---

## Milestone 1 — Dataset Pipeline

**Objective:** Obtain and reproducibly prepare the authoritative dataset.

**Tasks:** identify source; investigate 900 vs 5,572/5,169 discrepancy; verify provenance/schema/license; clean; deduplicate; validate labels; split without leakage; version dataset manifest.

**Files:** `src/ml/data/`, `configs/dataset.yaml`, `tests/test_dataset_pipeline.py`, `docs/dataset.md`; raw/processed data locations as appropriate.

**Dependencies:** authoritative dataset; Python/pandas/scikit-learn.

**Tests:** schema, duplicates, labels, missing values, reproducible split, leakage.

**Acceptance:** actual counts and provenance reconciled from source data; no fabricated records/labels.

**Expected commit:** `milestone-1: build reproducible dataset pipeline`

---

## Milestone 2 — Phishing ML

**Objective:** Implement the academic TF-IDF + SVM phishing baseline.

**Tasks:** text preprocessing; TF-IDF; SVM training; held-out evaluation; artifact/version management; calibration only if probability semantics are required.

**Files:** `src/ml/phishing/`, `models/phishing/`, `configs/phishing.yaml`, `tests/test_phishing_model.py`, `docs/ml-methodology.md`.

**Dependencies:** Milestone 1; scikit-learn and selected NLP libraries.

**Tests:** feature/schema tests, reproducibility, inference, evaluation, calibration where applicable.

**Acceptance:** reproducible baseline and honest held-out evaluation; raw SVM decision scores are not called probabilities.

**Expected commit:** `milestone-2: implement phishing ML baseline`

---

## Milestone 3 — Priority ML

**Objective:** Build the VADER + engineered features + Logistic Regression priority baseline for eligible non-phishing mail.

**Tasks:** define proxy labels; feature extraction; VADER; Logistic Regression; P1/P2/P3 evaluation; limitations.

**Files:** `src/ml/priority/`, `models/priority/`, `configs/priority.yaml`, `tests/test_priority_model.py`.

**Dependencies:** Milestones 1–2; VADER; scikit-learn.

**Tests:** feature extraction, labels, inference, held-out evaluation, regression.

**Acceptance:** priority model is separate from security classification; proxy labels are not presented as human judgment.

**Expected commit:** `milestone-3: implement priority ML baseline`

---

## Milestone 4 — Security Engine

**Objective:** Build the enhanced security analysis and decision layer around the academic baseline.

**Tasks:** safe MIME/header parsing; security indicators; URL/attachment metadata analysis; deterministic rules; combine ML evidence and security signals; controlled outcomes: PHISHING, SUSPICIOUS, NON-PHISHING, REVIEW REQUIRED.

**Files:** `src/security/`, `src/parsing/`, `src/domain/`, `configs/security.yaml`, `tests/security/`, `docs/threat-model.md`.

**Dependencies:** Milestones 1–3.

**Tests:** malformed MIME/header, URL/SSRF, attachment safety, rules, decision boundaries.

**Acceptance:** security classification happens before priority; no attachment execution; no automatic URL visits; SSRF protections; safe logging.

**Expected commit:** `milestone-4: add security analysis and decision engine`

---

## Milestone 5 — FastAPI Backend

**Objective:** Expose the analysis system through a validated API.

**Tasks:** FastAPI app; schemas; analysis endpoint; health/readiness; validation; safe errors/logging; persistence service abstraction; authentication/authorization as required.

**Files:** `backend/app/`, `backend/tests/`, backend dependency manifest, `configs/`.

**Dependencies:** Milestones 1–4.

**Tests:** unit, API contract, negative-input, auth/security regression tests.

**Acceptance:** secure API contract without secret or unnecessary body leakage.

**Expected commit:** `milestone-5: add secure FastAPI backend`

---

## Milestone 6 — React Dashboard

**Objective:** Provide a safe interface for security and priority results.

**Tasks:** React/Vite app; inbox/results; message detail; security signals; review queue; priority display only when eligible; API client; safe email rendering.

**Files:** `frontend/`, `frontend/src/`, `frontend/tests/`.

**Dependencies:** Milestone 5; Node.js/npm.

**Tests:** component, API integration, sanitization, accessibility.

**Acceptance:** security result is clearly separate from priority; untrusted email content is safely rendered.

**Expected commit:** `milestone-6: add React security dashboard`

---

## Milestone 7 — Email Integrations

**Objective:** Connect providers through one provider-neutral abstraction.

**Tasks:** define MailProvider interface; Gmail API adapter; Microsoft Graph adapter; IMAP adapter where required; OAuth/token lifecycle; least-privilege scopes; normalization; timeout/retry/rate-limit handling.

**Files:** `src/integrations/mail/`, provider adapters, `tests/integrations/`, `docs/mail-integrations.md`.

**Dependencies:** Milestone 5; provider APIs/SDKs.

**Tests:** adapter contracts, mocked providers, token handling, failures/retries, controlled provider integration tests.

**Acceptance:** interchangeable adapters; no stored passwords; secrets outside source control.

**Expected commit:** `milestone-7: add mail-provider abstraction and integrations`

---

## Milestone 8 — Docker + DevSecOps

**Objective:** Containerize the system and automate quality/security checks.

**Tasks:** Docker; local orchestration where useful; lint/format/type checks; tests; dependency scanning; secret scanning; pinned/locked dependencies.

**Files:** `Dockerfile`, orchestration config, `.dockerignore`, `.github/workflows/`, lockfiles, `docs/deployment.md`.

**Dependencies:** Milestones 5–7.

**Tests:** image build, smoke tests, CI, vulnerability scan, secret scan.

**Acceptance:** reproducible build and clean/triaged CI security checks.

**Expected commit:** `milestone-8: containerize and add DevSecOps CI`

---

## Milestone 9 — Security/Integration Testing

**Objective:** Validate the complete system against functional and security requirements.

**Tasks:** end-to-end tests; malformed/adversarial input; SSRF; attachment safety; auth; rate limits; provider integration; ML regression; false-positive/false-negative review; residual-risk documentation.

**Files:** `tests/e2e/`, `tests/security/`, `tests/integration/`, `docs/test-report.md`.

**Dependencies:** Milestones 1–8.

**Tests:** full automated suite plus controlled manual security testing.

**Acceptance:** critical issues resolved or explicitly release-blocked; regression suite passes; limitations documented.

**Expected commit:** `milestone-9: complete security and integration validation`

---

## Milestone 10 — Deployment

**Objective:** Deploy the validated system to a controlled production environment.

**Tasks:** hosting choice; external secret management; database/network/TLS configuration; deployment; monitoring; backups; rollback; least-privilege production mail credentials; smoke tests.

**Files:** `infra/` or provider-specific deployment config; `docs/deployment.md`; `docs/operations.md`.

**Dependencies:** Milestones 1–9.

**Tests:** production smoke, health, auth, mail integration, rollback.

**Acceptance:** reproducible deployment with TLS, managed secrets, access controls, monitoring and rollback.

**Expected commit:** `milestone-10: deploy validated IESP system`

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

**Milestone 0 stop rule:** do not begin Milestone 1 or create ML/application implementation until explicitly instructed.
