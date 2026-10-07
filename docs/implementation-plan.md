# IESP Master Implementation Status

The project uses `main` as the stable production/reference branch. The former `final-design` hardening branch was merged into `main` and is no longer the deployment source.

## M0 — Repository Audit + Architecture

**VERIFIED.** Repository structure, Git history, existing ML/security/backend code, configuration, tests, documentation and architecture were audited before extending the implementation. Existing M1/M2 foundations were preserved.

## M1 — Dataset + ML Pipeline

**VERIFIED.** The accepted M1 contract remains unchanged: deterministic preprocessing, exact duplicate removal, fingerprint validation, stratified 70/15/15 splitting, cross-split leakage checking and label validation. The authoritative dataset remains external to Git.

## M2 — Security Analysis Engine

**VERIFIED.** Safe MIME/header parsing, structural URL analysis, metadata-only attachment policy, HTML structural analysis, explainable reasons, fail-closed decisioning, explicit priority eligibility, and the TF-IDF + LinearSVC phishing baseline are integrated. The published runtime model artifacts are verified through the model-release workflow.

## M3 — Backend + Database

**HARDENED.** FastAPI exposes authentication, analysis, history, statistics, reports, provider OAuth and readiness endpoints. Strict validation, request limits, request IDs, safe errors, restrictive CORS, server-side sessions, workspace authorization and SQLite/PostgreSQL persistence are implemented.

## M4 — React Dashboard

**HARDENED.** React + Vite provides registration/login, dashboard, manual and `.eml` analysis, result transparency, history, reports, settings and logout. Email HTML is treated as untrusted text/structure rather than trusted DOM.

## M5 — Gmail / Microsoft Integration

**IMPLEMENTED.** Provider-neutral contracts, read-only Gmail/Microsoft adapters, OAuth state binding, PKCE, encrypted provider-token storage, connection management and provider-message analysis routes are present. Live external consent remains dependent on real provider-console credentials and redirect configuration.

## M6 — Testing + Security Testing

**HARDENED / VERIFIED BY CI.** Backend tests, PostgreSQL integration, frontend tests/build, dependency auditing, secret scanning, API contract validation and Docker verification are part of the repository CI gates.

## M7 — Deployment

**HARDENED.** Render deployment configuration defines the production backend, frontend static site and PostgreSQL resources. Production session/security settings, CORS wiring, model-artifact configuration, SPA fallback and security headers are defined in `render.yaml`.

Current Render production services:
- frontend display name: `iesp-home`
- frontend URL: `https://iesp-frontend.onrender.com`
- backend: `iesp-backend`
- production branch: `main`

## M8 — Documentation + Demonstration

**READY.** README, architecture, API, deployment, threat-model, limitations, current-state and product demonstration material are maintained as release documentation.

## End-to-end invariant

```text
Provider adapter → Safe parsing → Security features + phishing evidence → Security decision
→ PHISHING / SUSPICIOUS / REVIEW REQUIRED / NON-PHISHING
→ Priority eligibility → P1 / P2 / P3 only for NON-PHISHING → FastAPI → React
```

The release is complete only for the parts that have either been implemented or actually verified. External verification boundaries are recorded rather than fabricated.
