# IESP

## Intelligent Email Security & Prioritization System

IESP is a security-first academic cybersecurity SaaS prototype that combines deterministic email-security analysis, phishing ML evidence, transparent priority scoring, a FastAPI backend, a React dashboard, PostgreSQL persistence, and read-only Gmail/Microsoft Graph integrations.

## Architecture

```text
Email / Gmail / Microsoft
          ↓
Safe parsing + normalization
          ↓
Security feature extraction
          ↓
TF-IDF + LinearSVC phishing evidence
          ↓
Security policy decision
  ├─ PHISHING
  ├─ SUSPICIOUS
  ├─ REVIEW REQUIRED
  └─ NON-PHISHING
          ↓
Priority eligibility
          ↓
P1 / P2 / P3
          ↓
FastAPI + PostgreSQL
          ↓
React dashboard
```

Priority is never returned for PHISHING, SUSPICIOUS, or REVIEW REQUIRED.

## Current GitHub / deployment state

`main` is the current release/deployment branch. The `final-design` branch was the hardening branch and has been merged into `main`; `main` is the production/reference branch.

Render is configured from `render.yaml` and pins both the backend and frontend services to `main`.

## M0–M8 status

| Milestone | Status | Evidence boundary |
|---|---|---|
| M0 Repository audit + architecture | VERIFIED | Repository structure and architecture were reviewed and documented |
| M1 Dataset + ML pipeline | VERIFIED | Reproducible split/fingerprint contract and model-release workflow are preserved |
| M2 Security analysis engine / phishing ML | VERIFIED | Deterministic security engine and model-release assets are integrated |
| M3 Backend + database | HARDENED | Session authentication, strict validation, workspace scoping, SQLite + PostgreSQL |
| M4 React dashboard | HARDENED | Feature-based UI, safe rendering, responsive/accessibility improvements |
| M5 Gmail / Microsoft integration | IMPLEMENTED | Provider OAuth routes, state binding, PKCE, encrypted token storage, read-only adapters |
| M6 Testing + security testing | HARDENED | Backend/frontend/security/contract tests and dependency/secret checks are part of CI |
| M7 Deployment | HARDENED | Docker, Render Blueprint, health/readiness checks, production environment validation |
| M8 Documentation + presentation | READY | README, demo flow, architecture explanation, and viva material can be derived from this implementation |

## Machine-learning baseline

### Phishing

TF-IDF word unigrams/bigrams + LinearSVC. The SVM `decision_function` value is a ranking margin, not a calibrated probability.

### Priority

VADER sentiment + engineered email features + Logistic Regression. P1/P2/P3 are project proxy labels, not human-annotated urgency ground truth.

## Security controls

- Email content is treated as untrusted data.
- HTML is analyzed structurally and is never rendered as trusted DOM.
- URLs are inspected structurally and are never automatically visited.
- Local/private destinations are escalated as SSRF-sensitive.
- Attachments are metadata-only and are never executed.
- Request and email size limits are enforced.
- Analysis endpoints are rate limited.
- Browser authentication uses an HTTP-only session cookie; no browser API key is required.
- Session tokens are hashed server-side.
- Production requires HTTPS/Secure cookies and explicit CORS origins.
- Provider OAuth uses authorization state binding and PKCE.
- Provider access/refresh tokens are encrypted at rest and never returned to browser JavaScript.
- Logs exclude passwords, session tokens, API keys, raw email bodies, and attachment contents.
- Production API responses use restrictive security headers and `Cache-Control: no-store` for API routes.

## API surface

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Analysis
- `POST /api/v1/analyze`
- `POST /api/v1/analyze/raw`
- `POST /api/v1/analyze/eml`
- `GET /api/v1/history`
- `GET /api/v1/recent?limit=20`
- `GET /api/v1/analysis/{message_id}`
- `GET /api/v1/stats`

### Reports
- `GET /api/v1/reports/summary`
- `GET /api/v1/reports/export?format=csv|json`

### Provider OAuth
- `GET /api/v1/oauth/gmail/start`
- `GET /api/v1/oauth/gmail/callback`
- `GET /api/v1/oauth/microsoft/start`
- `GET /api/v1/oauth/microsoft/callback`
- `GET /api/v1/oauth/connections`
- `DELETE /api/v1/oauth/{provider}`
- `GET /api/v1/oauth/{provider}/messages`
- `POST /api/v1/oauth/{provider}/messages/{message_id}/analyze`

### Operations
- `GET /health`
- `GET /ready`

## Live demo

Production frontend: `https://iesp-frontend.onrender.com`  
Render service display name: `iesp-home`  
Production backend: `https://iesp-backend.onrender.com`

The Render service is named `iesp-home`, while its existing Render-managed subdomain remains `iesp-frontend.onrender.com`. This does not affect application behavior.

For a repeatable demonstration, use the production frontend URL above and a prepared `.eml` sample.

## .eml demo workflow

IESP accepts bounded `.eml` files. The browser checks the extension and size before submission, while the backend performs safe MIME parsing. Submitted HTML is never rendered. Analysis results store metadata/results rather than raw message bodies.

A simple demo file can contain headers such as:

```text
From: security-alert@example.com
To: student@example.com
Subject: Urgent account verification

Your account requires verification.
Visit https://example.com/verify
```

Save the message as `sample-phishing.eml` and upload it from the Analyze page.

## Gmail / Microsoft OAuth

The provider flow is intentionally read-only. The backend creates short-lived OAuth state bound to the authenticated session, uses PKCE, validates Microsoft OIDC identity, exchanges the authorization code server-side, encrypts provider tokens at rest, and exposes only connection metadata to the browser.

For a live deployment, the following Render secrets must be configured:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `MICROSOFT_REDIRECT_URI`

`IESP_OAUTH_ENCRYPTION_KEY` is generated by the Render Blueprint.

The redirect URIs must exactly match the provider-console configuration.

## Render deployment

The repository contains a Render Blueprint with:

- backend Docker web service
- frontend static site
- PostgreSQL database
- production session settings
- explicit CORS origin wiring
- generated OAuth encryption key
- OAuth provider secret placeholders
- backend `/ready` health check
- SPA fallback routing
- frontend security headers

After environment variables are configured, verify:

1. backend deploy status is Live
2. `/health` returns success
3. `/ready` reports ready
4. frontend opens successfully
5. login/session flow works
6. Gmail OAuth and Microsoft OAuth are tested end-to-end with real provider credentials

## Local development

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt -r requirements-api.txt
export IESP_ENVIRONMENT=development
uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

No API key is required by browser code. Authentication is established through the HTTP-only session cookie.

## Demo / presentation flow

Use this order for a 5–8 minute college demo:

```text
1. Open dashboard
2. Register / Login
3. Show Analyze page
4. Upload sample .eml
5. Explain classification + risk reasons
6. Open History
7. Open Reports
8. Open Settings
9. Show Gmail / Microsoft connection controls (live provider OAuth only when provider credentials are configured and the flow has been tested)
10. Logout
```

Recommended talking points:

- Problem: phishing and malicious emails are difficult to triage safely.
- Solution: combine ML evidence with deterministic security rules.
- Security principle: untrusted email content must never become executable browser content.
- Authentication: server-side sessions with HTTP-only cookies.
- OAuth: state + PKCE + server-side encrypted token storage.
- ML limitation: SVM margin is evidence/ranking, not a probability.
- Priority limitation: P1/P2/P3 are proxy project labels.
- Deployment: React frontend + FastAPI backend + PostgreSQL on Render.

## Research integrity

Only claim results that were actually observed. Do not present model accuracy, F1, ROC-AUC, provider-success, deployment-success, or security-test outcomes unless the corresponding execution was run and recorded.

## License / academic use

IESP is presented as an academic cybersecurity project and demonstration platform. Production use would require additional operational controls such as stronger secret management, monitoring/alerting, privacy/legal review, and a production-grade rate-limit/session infrastructure.
