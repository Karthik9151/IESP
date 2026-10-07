# IESP

## Intelligent Email Security & Prioritization System

IESP is a security-first academic prototype that combines deterministic email security analysis, a phishing ML baseline, transparent priority scoring, a FastAPI backend, a React dashboard, and read-only Gmail/Microsoft Graph adapters.

## Security-first decision flow

\`\`\`text
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
\`\`\`

Priority is never returned for PHISHING, SUSPICIOUS, or REVIEW REQUIRED.

## Repository workflow

\`furnished-design\` is the current hardening branch for this implementation. \`main\` remains the stable/reference branch. Milestones are stages, not long-lived branches.

## M0–M8 status

| Milestone | Status | Evidence boundary |
|---|---|---|
| M0 Repository audit + architecture | VERIFIED | Repository structure, architecture and source-of-truth docs retained |
| M1 Dataset + ML pipeline | VERIFIED | Accepted fingerprint/splits and reproducible pipeline are preserved |
| M2 Security analysis engine / phishing ML | VERIFIED | Existing verified model-release workflow and \`models-v1\` assets preserved |
| M3 Backend + database | HARDENED | Secure session auth, strict validation, workspace-scoped persistence, SQLite + PostgreSQL |
| M4 React dashboard | HARDENED | Feature-based React UI, safe text rendering, responsive/accessibility improvements |
| M5 Gmail / Outlook integration | IMPLEMENTED | Read-only adapters + OAuth helpers; live provider credentials not tested here |
| M6 Testing + security testing | HARDENED | Blocking backend/frontend/security/contract CI gates added |
| M7 Deployment | HARDENED / PARTIALLY VERIFIED | Docker, Compose, Render config, runtime model bootstrap; live deployment not verified |
| M8 Documentation + presentation | UPDATED | API, architecture, deployment and current-state docs synchronized |

## Preserved M1 contract

- Dataset: \`meajor_cleaned_preprocessed.parquet.gzip\`
- Project fingerprint: \`34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582\`
- Train: \`76069\`
- Validation: \`16300\`
- Test: \`16301\`
- 70/15/15 stratified split, random state 42
- exact full-record deduplication and cross-split fingerprint leakage checks
- authoritative dataset intentionally excluded from GitHub

## ML baselines

### Phishing
TF-IDF word unigrams/bigrams + LinearSVC. \`decision_function\` is a ranking margin, not a probability.

### Priority
VADER + engineered email features + Logistic Regression. P1/P2/P3 are deterministic proxy/project labels, not human urgency annotations.

## Verification status

The \`furnished-design\` CI pipeline has a completed PASS run covering backend/security tests, frontend tests/build, dependency audits, full-history secret scanning, generated OpenAPI contract validation, real PostgreSQL 16 integration tests, and Docker image builds. Live Render/browser deployment and live provider OAuth remain unverified.

## Security controls

Email content is treated only as untrusted data. Attachments are metadata-only and never executed. URLs are inspected structurally and never automatically visited. Local/private destinations are escalated as SSRF-sensitive. HTML is analyzed as text and is never rendered by the dashboard.

Authentication uses a server-side session identified by an HTTP-only cookie. The browser has no API-key or bearer-token shortcut. Production requires a Secure cookie and explicit CORS origins. Session tokens are stored only as hashes server-side.

Logs exclude passwords, session tokens, API keys, raw email bodies and attachment contents.

## API

- \`GET /health\`
- \`GET /ready\`
- \`POST /api/v1/auth/register\`
- \`POST /api/v1/auth/login\`
- \`POST /api/v1/auth/logout\`
- \`GET /api/v1/auth/me\`
- \`POST /api/v1/analyze\`
- \`POST /api/v1/analyze/raw\`
- \`POST /api/v1/analyze/eml\`
- \`GET /api/v1/stats\`
- \`GET /api/v1/recent?limit=20\`
- \`GET /api/v1/history\`
- \`GET /api/v1/analysis/{message_id}\`
- \`GET /api/v1/reports/summary\`
- \`GET /api/v1/reports/export?format=csv|json\`

Analysis lookups and aggregate data are scoped by the authenticated workspace.

## Run locally

Backend:

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt -r requirements-api.txt
export IESP_ENVIRONMENT=development
uvicorn backend.app.main:app --reload
\`\`\`

Frontend:

\`\`\`bash
cd frontend
npm ci
npm run dev
\`\`\`

No API key is required by the browser. Authentication is established by the HTTP-only session cookie.

The backend reports \`/ready\` as unavailable until required model artifacts are available.

## .eml workflow

The Analyze page supports paste-based analysis and bounded \`.eml\` upload. The browser validates extension/size, prevents duplicate submission, supports cancellation, and never renders submitted HTML. The backend performs safe MIME parsing and stores analysis metadata/results rather than raw message bodies.

## Provider integrations

\`src/providers/\` contains provider-neutral interfaces, Gmail and Microsoft Graph read-only adapters, normalization helpers, and OAuth state/PKCE helpers. Live provider validation requires external application configuration and user consent and is not claimed as completed here.

## Research integrity

No accuracy, F1, ROC-AUC, PR-AUC, provider-success, deployment-success, or security-test result is claimed unless that execution was actually observed. External blockers are recorded as pending/not verified rather than hidden.
