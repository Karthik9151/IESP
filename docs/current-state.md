# Current Repository State

**Audit date:** 2026-10-07  
**Repository:** \`Karthik9151/IESP\`  
**Working branch:** \`furnished-design\`

## Hardening status

| Area | Status | Notes |
|---|---|---|
| M0–M2 dataset/ML/security foundations | PRESERVED | Existing domain models and security engine remain the source of truth |
| Backend compatibility | HARDENED | Service/API now call the real engine/model APIs |
| Authentication | HARDENED | Server-side session + HTTP-only cookie; browser API-key path removed |
| Authorization | HARDENED | Analysis/history/stats/report lookups are workspace-scoped |
| SQLite repository | HARDENED | Sender/recipients/subject/model score/version metadata are persisted |
| PostgreSQL repository | VERIFIED | Real PostgreSQL 16 CI service exercised schema, auth/session/expiry, metadata persistence, workspace isolation, and transaction rollback |
| Error contract | HARDENED | Nested error object with request ID and optional retry metadata |
| Rate limiting | IMPLEMENTED | Per-user in-memory 429 + Retry-After; distributed store remains future work |
| \`.eml\` backend | HARDENED | Bounded stdlib MIME parsing, no execution/network access |
| Frontend | HARDENED | Analyze/.eml/history/dashboard/reports/settings feature structure |
| Result transparency | HARDENED | Policy risk score is distinct from ML decision margin |
| Accessibility/mobile | HARDENED | Semantic labels, focus treatment, 44px-class controls, responsive layouts |
| Security headers/CSP | HARDENED | Nginx + Render headers; production HSTS |
| CI/CD | HARDENED | Blocking test/build/security/contract jobs |
| Model release | PRESERVED | Existing \`models-v1\` bootstrap and verification flow retained |
| External deployment | NOT VERIFIED | Render production endpoint/browser flow was not accessible from the current environment |
| Live provider OAuth | NOT VERIFIED | Requires user-owned provider registration and consent |

## Verification evidence

- Completed CI run **37588346379** on `furnished-design`: PASS.
- Backend/security: PASS — `pytest -q -ra`.
- Frontend: PASS — `npm ci`, `npm test`, `npm run build`, and `npm audit --audit-level=high`.
- Python dependency audit: PASS — `pip-audit -r requirements-ml.txt -r requirements-api.txt`; dependency consistency: PASS — `python -m pip check`.
- Secret scan: PASS — full-history Gitleaks scan.
- API contract: PASS — generated OpenAPI route, schema, error, pagination, report, and session-cookie security validation.
- PostgreSQL: PASS — five real integration tests against a PostgreSQL 16 service.
- Docker: PASS — backend and frontend images built successfully.
- Browser E2E, live Render deployment, and live provider OAuth remain unverified.

## Known repository constraints

1. \`frontend/package-lock.json\` is committed and deterministic Node dependency installation is enforced with \`npm ci\` in CI, the frontend image, and Render.
2. Live Render deployment and production browser/API behavior are not verified in this environment.
3. Live Gmail/Microsoft OAuth requires external application configuration/consent.
4. Legacy analysis rows from the pre-hardening schema may retain empty sender/subject values because those values were never stored. New analyses persist actual metadata.

## Security invariants

Security runs before priority. Priority is only eligible after \`NON-PHISHING\`. Parser failures and critical findings fail closed. URLs are never automatically fetched. Attachments are metadata-only. HTML is never rendered as trusted DOM. Secrets and raw email bodies are excluded from analysis logs.
