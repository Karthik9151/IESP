# IESP API — Milestone 5

## Base endpoints

GET /health is public and reports service health.

GET /ready reports whether the phishing and priority model services are available. It returns 503 with blocker codes when required model artifacts are unavailable.

POST /api/v1/analyze requires X-API-Key unless authentication is explicitly disabled in development/test mode.

## Request contract

The analyze request requires message_id, sender and at least one recipient. Subject, text_body, html_body, headers, attachment metadata and received_timestamp are optional. Extra JSON fields are rejected.

Configured limits include a 1 MiB default request body limit, 500,000 characters per text/html body, 50 recipients, 100 headers, 25 attachments, and 50 extracted URLs. Header names/values reject carriage returns, NULs and invalid header names.

## Response contract

The response separates security from priority:

{
  "message_id": "...",
  "request_id": "...",
  "security": {
    "classification": "NON-PHISHING",
    "reasons": []
  },
  "priority": {
    "label": "P2",
    "proxy_label": true
  }
}

For PHISHING, SUSPICIOUS or REVIEW REQUIRED, priority is null.

SVM raw decision scores are not returned in the public response.

## Authentication and authorization

The API key is supplied by environment configuration and compared using constant-time comparison. Secrets are not hard-coded or logged. The service layer has an authorization boundary even though the MVP has one analysis role.

## Errors

Client validation errors use 422. Oversized requests use 413. Missing/invalid API keys use 401. Authorization failures use 403. Unexpected failures return a generic 500 response with a request ID and no stack trace, file path or secret.

## CORS

Allowed browser origins come from IESP_ALLOWED_ORIGINS. Credentials are disabled and wildcard origins are not used.

## Persistence boundary

AnalysisRepository is defined as a service abstraction. M5 uses a no-op implementation, so production database persistence is not claimed as implemented.
