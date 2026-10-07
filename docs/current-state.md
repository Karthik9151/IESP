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
| Phishing ML | VERIFIED | Authoritative MeAJOR run completed through model-release automation; verified artifacts published |
| Priority ML | IMPLEMENTED | VADER + engineered features + Logistic Regression + proxy labels |
| Security engine | VERIFIED | MIME/header, URL, attachment, HTML and fail-closed decisioning |
| Backend | VERIFIED | FastAPI, auth, validation, SQLite metadata repository, safe errors |
| Frontend | IMPLEMENTED | React/Vite dashboard with safe text display |
| Gmail adapter | IMPLEMENTED | Read-only retrieval, raw MIME parsing |
| Microsoft Graph adapter | IMPLEMENTED | Read-only retrieval and attachment metadata |
| OAuth helpers | IMPLEMENTED | State validation and PKCE helper; token storage remains external |
| Testing | VERIFIED by CI baseline | CI #47 passed critical backend tests, regression job, dependency audit, frontend build/tests and secret scan |
| Docker | IMPLEMENTED | Model-aware backend image; model release is bootstrapped at container startup; frontend image and Compose |
| CI/CD | VERIFIED by CI baseline | CI #47 is the current green baseline |
| Model release automation | VERIFIED | Release workflow #16 completed successfully and verified the published `models-v1` assets |
| External deployment | PENDING | Render rebuild/restart still needs observed success with the published models |
| Live provider OAuth validation | PENDING | Requires user-owned provider app credentials and consent |

## Verified release evidence

The authoritative model-release workflow completed successfully as run **#16** on commit `1b84ff5f2a8d33b22cab6294b085d97e8964cb21`.

The run successfully:
- downloaded the authoritative MeAJOR dataset;
- verified MD5 `78e397ad8447bcdba5a98097921ba8bd`;
- ran the accepted M1 pipeline;
- trained and validated phishing and priority models;
- built the release manifest;
- checked artifact size limits;
- published `models-v1`;
- verified the expected release assets.

The published manifest retains the accepted M1 fingerprint:

`34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582`

with splits: train **76,069**, validation **16,300**, test **16,301**.

## Genuine blockers

1. The live Render instance must be rebuilt/restarted so startup bootstrap can obtain and verify the published runtime artifacts.
2. Live Gmail/Outlook OAuth requires external application registration and user consent.

## Security invariants

Security runs before priority; priority is possible only after NON-PHISHING; parser failure and critical signals fail closed; URLs are not automatically fetched; attachments are not executed; secrets and full email content are not logged; the authoritative dataset stays outside Git history.
