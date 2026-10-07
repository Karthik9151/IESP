# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** `Karthik9151/IESP`  
**Release branch:** `main`

## Release status

| Area | Status | Notes |
|---|---|---|
| M0–M2 dataset/ML/security foundations | VERIFIED | Existing domain models, security engine, dataset contract and model-release artifacts are preserved |
| Backend compatibility | HARDENED | FastAPI calls the real engine/model APIs |
| Authentication | HARDENED | Server-side session + HTTP-only cookie; browser API-key path removed |
| Authorization | HARDENED | Analysis/history/stats/report lookups are workspace-scoped |
| SQLite repository | HARDENED | Analysis metadata and security results are persisted |
| PostgreSQL repository | VERIFIED | PostgreSQL CI coverage exercises schema, auth/session/expiry, metadata persistence, workspace isolation and rollback |
| Error contract | HARDENED | Structured errors include request ID and optional retry metadata |
| Rate limiting | IMPLEMENTED | Per-user in-memory 429 + Retry-After; distributed rate limiting remains future infrastructure |
| `.eml` backend | HARDENED | Bounded stdlib MIME parsing with no execution or automatic network access |
| Frontend | HARDENED | Analyze/.eml/history/dashboard/reports/settings flows |
| Result transparency | HARDENED | Security policy risk score is distinct from ML decision margin |
| Accessibility/mobile | HARDENED | Semantic labels, focus treatment and responsive layouts |
| Security headers/CSP | HARDENED | Render security headers and restrictive CSP are configured |
| CI/CD | HARDENED | Blocking test/build/security/contract jobs are configured |
| Model release | PRESERVED | Existing `models-v1` bootstrap and verification flow retained |
| OAuth | IMPLEMENTED | Gmail/Microsoft routes, state binding, PKCE and encrypted provider-token storage are present; live external consent is environment-dependent |
| Production Render deployment | VERIFIED | Backend and frontend services are configured on Render and the production frontend is live |
| Manual UI smoke flow | VERIFIED | Registration, login, dashboard, analysis, result display, history, reports, settings, logout, invalid login and invalid analysis were manually exercised |

## Production Render state

- Frontend service display name: `iesp-home`
- Existing Render-managed frontend URL: `https://iesp-frontend.onrender.com`
- Backend URL: `https://iesp-backend.onrender.com`
- Both production services track `main`
- Frontend build command: `cd frontend && npm ci && npm run build`
- Frontend publish directory: `./frontend/dist`
- Backend health/readiness paths: `/health` and `/ready`

The frontend service display name is `iesp-home`, while the existing Render subdomain remains `iesp-frontend.onrender.com`. The URL difference is a Render naming/subdomain detail, not an application defect.

## Verification evidence

- Frontend hardening CI completed successfully before merge.
- PR #14 from `final-design` to `main` was merged.
- Production frontend and backend Render services are configured against `main`.
- Manual UI smoke testing covered the core authenticated workflow and negative cases.

## Remaining verification boundary

Live Gmail/Microsoft provider consent should only be claimed after a real provider-console configuration has been exercised end-to-end. The same rule applies to any new browser-E2E or production API measurements: record observed results rather than inferring them.

## Security invariants

Security runs before priority. Priority is only eligible after `NON-PHISHING`. Parser failures and critical findings fail closed. URLs are never automatically fetched. Attachments are metadata-only. HTML is never rendered as trusted DOM. Secrets, session tokens and raw email bodies are excluded from analysis logs.