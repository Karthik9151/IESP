# IESP API

## Endpoints

- `GET /health` — public health.
- `GET /ready` — model readiness; returns 503 with blocker codes when required artifacts are absent.
- `POST /api/v1/analyze` — authenticated email analysis.
- `GET /api/v1/stats` — authenticated aggregate counts.
- `GET /api/v1/recent?limit=20` — authenticated analysis metadata.
- `GET /api/v1/analysis/{message_id}` — authenticated stored result metadata.

## Analyze request

Required: `message_id`, `sender`, and at least one `recipients` entry. Optional: subject, text body, HTML body, headers, attachment metadata and received timestamp. Extra JSON fields are rejected. Size and count limits protect the service.

## Analyze response

```json
{
  "message_id": "m1",
  "request_id": "req-1",
  "security": {"classification": "NON-PHISHING", "reasons": []},
  "priority": {"label": "P2", "proxy_label": true},
  "model_info": {"phishing": "TF-IDF + LinearSVC", "priority": "VADER + engineered features + Logistic Regression"}
}
```

For PHISHING, SUSPICIOUS and REVIEW REQUIRED, `priority` is `null`.

## Authentication

`session cookie` is sourced from environment configuration and checked with constant-time comparison. Keys are never hard-coded or logged. Production requires a configured API key.

## Error contract

401 auth failure; 403 authorization failure; 413 oversized request; 422 validation failure; 404 missing analysis; 500 generic internal error without sensitive details.
