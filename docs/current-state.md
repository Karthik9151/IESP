# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** `Karthik9151/IESP`  
**Active development branch:** `development`  
**Stable/reference branch:** `main`

## Implementation status

| Layer | Status | Notes |
|---|---|---|
| Repository audit / architecture | VERIFIED | Consolidated on `development` |
| M1 data pipeline | VERIFIED | Accepted fingerprint and split contract retained |
| Phishing ML | PARTIALLY VERIFIED | Reproducible implementation exists; real-data run is blocked when the authoritative dataset is absent |
| Priority ML | IMPLEMENTED | VADER + engineered features + Logistic Regression + proxy labels |
| Security engine | VERIFIED | MIME/header, URL, attachment, HTML and fail-closed decisioning |
| Backend | VERIFIED | FastAPI, auth, validation, SQLite metadata repository, safe errors |
| Frontend | IMPLEMENTED | React/Vite dashboard with safe text display |
| Gmail adapter | IMPLEMENTED | Read-only retrieval, raw MIME parsing |
| Microsoft Graph adapter | IMPLEMENTED | Read-only retrieval and attachment metadata |
| OAuth helpers | IMPLEMENTED | State validation and PKCE helper; token storage remains external |
| Testing | IMPLEMENTED / PARTIALLY VERIFIED | Unit/integration/security suites plus CI automation |
| Docker | IMPLEMENTED | Backend and frontend images plus Compose |
| CI/CD | IMPLEMENTED | Test, compile, dependency-audit and secret-scan jobs |
| External deployment | PENDING | Not executed in this environment |
| Live provider OAuth validation | PENDING | Requires user-owned provider app credentials and consent |

## Structure

```text
IESP/
├── backend/app/
├── frontend/
├── src/domain/
├── src/parsing/
├── src/security/
├── src/ml/data/
├── src/ml/phishing/
├── src/ml/priority/
├── src/providers/
├── configs/
├── data/
├── models/
├── scripts/
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Preserved M1 record

Raw 108,685; usable 108,683; exact duplicate copies 13; final unique 108,670; benign 60,636; phishing 48,034. Accepted fingerprint: `34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582`; splits 76,069 / 16,300 / 16,301.

## Genuine blockers

1. The authoritative MeAJOR Parquet is not stored in GitHub, so final real-data M2 execution must be performed where that exact file is available.
2. Docker is not installed in the current runtime, so container build verification cannot be claimed locally.
3. Live Gmail/Outlook OAuth requires external application registration and user consent; mocked adapter tests cover the adapter contract instead.

## Security invariants

Security runs before priority; priority is possible only after NON-PHISHING; parser failure and critical signals fail closed; URLs are not automatically fetched; attachments are not executed; secrets and full email content are not logged; the authoritative dataset stays outside Git history.
