# IESP API

## Authentication

Protected \`/api/v1/*\` endpoints require a valid server-side session cookie. Registration and login establish the session; logout is intentionally idempotent and clears the current cookie even when no valid session is present.

Login or registration sets an HTTP-only cookie. The browser does not send an API key or bearer token. In production the cookie is Secure and the deployment uses explicit CORS origins.

## Endpoints

- \`GET /health\` — public liveness.
- \`GET /ready\` — readiness; returns 503 when required model/database dependencies are unavailable.
- \`POST /api/v1/auth/register\` — create account + workspace and establish session.
- \`POST /api/v1/auth/login\` — authenticate and establish session.
- \`POST /api/v1/auth/logout\` — invalidate the current session.
- \`GET /api/v1/auth/me\` — return authenticated account/workspace.
- \`POST /api/v1/analyze\` — analyze structured email content.
- \`POST /api/v1/analyze/raw\` — analyze raw textual email content.
- \`POST /api/v1/analyze/eml\` — analyze a bounded \`.eml\` upload.
- \`GET /api/v1/stats\` — workspace-scoped aggregate metrics.
- \`GET /api/v1/recent?limit=20\` — recent workspace analyses.
- \`GET /api/v1/history\` — paginated/filterable/sortable workspace history.
- \`GET /api/v1/analysis/{message_id}\` — workspace-scoped stored analysis detail.
- \`GET /api/v1/reports/summary\` — workspace-scoped summary report.
- \`GET /api/v1/reports/export?format=csv|json\` — metadata export.

## Analyze response

\`\`\`json
{
  "message_id": "m1",
  "request_id": "req-1",
  "analyzed_at": "2026-10-07T10:00:00Z",
  "email": {
    "message_id": "m1",
    "sender": "sender@example.com",
    "recipients": ["user@example.com"],
    "subject": "Hello"
  },
  "security": {
    "classification": "NON-PHISHING",
    "risk_score": 10,
    "model_score": -1.2,
    "model_score_kind": "decision_margin",
    "reasons": []
  },
  "priority": {
    "label": "P2",
    "proxy_label": true
  },
  "model_info": {
    "phishing": "TF-IDF + LinearSVC decision margin",
    "priority": "VADER + engineered features + Logistic Regression",
    "model_version": "models-v1",
    "policy_version": "policy-v1"
  }
}
\`\`\`

\`risk_score\` is the application's deterministic policy/risk score, not a probability. \`model_score\` is the underlying classifier decision margin when available.

Priority is returned only when the security classification is \`NON-PHISHING\` and the configured priority model is available.

## History filters

\`GET /api/v1/history\` supports page/page_size, sender/subject search, classification, min/max risk, date_from/date_to, and whitelisted sort fields/order.

## Error contract

\`\`\`json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "request_id": "req-1",
    "retry_after_seconds": null
  }
}
\`\`\`

The API uses 401 for missing/invalid sessions, 404 for workspace-scoped missing objects, 413 for oversized requests, 422 for validation/parse errors, 429 for rate limits, and 500 for sanitized internal failures.

OpenAPI exposes the session-cookie security scheme for protected operations, together with success, error, pagination, analysis, and report schemas.

Analysis rate limiting is currently in-memory and keyed by authenticated user. A Redis/provider-backed store can replace it later without changing the API contract.

## Trust boundary

\`.eml\` parsing is bounded and attachment metadata-only. HTML is analyzed structurally and never rendered as trusted DOM. URLs are inspected without network fetching. Session tokens, passwords and raw email bodies are never returned to the frontend or written to analysis logs.
