# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** `Karthik9151/IESP`  
**Primary branch:** `main`  
**Development branch:** `development`

## Implementation status

| Layer | Status | Notes |
|---|---|---|
| Repository audit / architecture | VERIFIED | Integrated architecture and source-of-truth docs retained |
| M1 data pipeline | VERIFIED | Accepted fingerprint and split contract retained |
| Phishing ML | PARTIALLY VERIFIED | Reproducible training path exists; runtime release pending execution |
| Priority ML | IMPLEMENTED | VADER + engineered features + Logistic Regression + proxy labels |
| Security engine | VERIFIED | MIME/header, URL, attachment, HTML and fail-closed decisioning |
| Backend | VERIFIED | FastAPI, auth, validation, SQLite metadata repository, safe errors |
| Frontend | IMPLEMENTED | React/Vite dashboard with safe text display |
| Gmail adapter | IMPLEMENTED | Read-only retrieval, raw MIME parsing |
| Microsoft Graph adapter | IMPLEMENTED | Read-only retrieval and attachment metadata |
| OAuth helpers | IMPLEMENTED | State validation and PKCE helper; token storage remains external |
| Testing | IMPLEMENTED / PARTIALLY VERIFIED | Unit/integration/security suites plus CI automation |
| Docker | IMPLEMENTED | Model-aware backend image; model release is bootstrapped at container startup; frontend image and Compose |
| CI/CD | IMPLEMENTED | Test, compile, dependency-audit and secret-scan jobs |
| Model release automation | IMPLEMENTED | Manual workflow plus automatic runs on relevant ML/M1 changes; publishes verified runtime artifacts |
| External deployment | PENDING | Render rebuild still needs observed success with published models |
| Live provider OAuth validation | PENDING | Requires user-owned provider app credentials and consent |

## Genuine blockers

1. The live Render instance must be rebuilt/restarted after `models-v1` is published so the startup bootstrap can obtain the verified runtime artifacts.
2. The model-release workflow must complete successfully before Render can become ready.
3. Live Gmail/Outlook OAuth requires external application registration and user consent.

## Security invariants

Security runs before priority; priority is possible only after NON-PHISHING; parser failure and critical signals fail closed; URLs are not automatically fetched; attachments are not executed; secrets and full email content are not logged; the authoritative dataset stays outside Git history.
