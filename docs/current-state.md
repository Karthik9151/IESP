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
| PostgreSQL repository | HARDENED | Explicit PostgreSQL schema/types/indexes; no SQLite-to-Postgres string replacement |
| Error contract | HARDENED | Nested error object with request ID and optional retry metadata |
| Rate limiting | IMPLEMENTED | Per-user in-memory 429 + Retry-After; distributed store remains future work |
| \`.eml\` backend | HARDENED | Bounded stdlib MIME parsing, no execution/network access |
| Frontend | HARDENED | Analyze/.eml/history/dashboard/reports/settings feature structure |
| Result transparency | HARDENED | Policy risk score is distinct from ML decision margin |
| Accessibility/mobile | HARDENED | Semantic labels, focus treatment, 44px-class controls, responsive layouts |
| Security headers/CSP | HARDENED | Nginx + Render headers; production HSTS |
| CI/CD | HARDENED | Blocking test/build/security/contract jobs |
| Model release | PRESERVED | Existing \`models-v1\` bootstrap and verification flow retained |
| External deployment | NOT VERIFIED | Render/production browser/PostgreSQL not exercised here |
| Live provider OAuth | NOT VERIFIED | Requires user-owned provider registration and consent |

## Verified local checks

- Python compile check: PASS.
- Targeted backend API/repository tests: PASS — 13 passed.
- Frontend API-client tests: PASS — 3 passed.
- Frontend pure JavaScript syntax checks: PASS for \`api.js\` and \`lib/security.js\`.
- One local command attempted a nonexistent copied \`frontend/tests/security.test.mjs\` file and therefore returned a nonzero shell status; the GitHub branch does contain that file.

## Known repository constraints

1. \`package-lock.json\` is not present, so deterministic Node dependency installation is not yet claimable.
2. Live Render and production PostgreSQL behavior are not verified in this environment.
3. Live Gmail/Microsoft OAuth requires external application configuration/consent.
4. Legacy analysis rows from the pre-hardening schema may retain empty sender/subject values because those values were never stored. New analyses persist actual metadata.

## Security invariants

Security runs before priority. Priority is only eligible after \`NON-PHISHING\`. Parser failures and critical findings fail closed. URLs are never automatically fetched. Attachments are metadata-only. HTML is never rendered as trusted DOM. Secrets and raw email bodies are excluded from analysis logs.
