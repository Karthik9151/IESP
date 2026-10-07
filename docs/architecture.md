# IESP Architecture

## Layered design

```text
Mail provider
    ↓
Provider adapter / normalizer
    ↓
Safe MIME + header parser
    ↓
Security feature extraction
    ├─ headers/authentication
    ├─ URL structure
    ├─ attachment metadata
    └─ HTML structure
    ↓
TF-IDF + LinearSVC phishing evidence
    ↓
Security Decision Engine
    ↓
PHISHING / SUSPICIOUS / REVIEW REQUIRED / NON-PHISHING
    ↓
Priority eligibility
    ↓
VADER + engineered features + Logistic Regression
    ↓
P1 / P2 / P3
    ↓
FastAPI
    ↓
React dashboard
```

Security classification is authoritative and precedes priority. Untrusted email is data, not executable instructions.

## Components

- Domain models: shared provider-neutral email/security types.
- Parsing: standard-library MIME parsing with size/defect checks.
- Security: header, URL, attachment and HTML analyzers plus configurable decision policy.
- ML: accepted M1 data pipeline, phishing classifier, proxy-label priority classifier.
- Backend: FastAPI validation/auth/service/repository boundary.
- Persistence: SQLite metadata repository for local and single-instance deployments; PostgreSQL is the production persistence tier.
- Frontend: React/Vite with safe text handling.
- Providers: Gmail and Microsoft Graph read-only adapters.
- Deployment: Docker/Compose and GitHub Actions.

## Data minimization

Only analysis metadata and reason evidence are persisted. Raw email bodies, HTML, attachments and provider tokens are not persisted by the application.

## Failure behavior

Parser errors and critical signals produce REVIEW REQUIRED. Missing phishing evidence fails closed when required. Provider failures become provider errors and cannot cause mailbox mutation.
