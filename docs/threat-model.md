# IESP Threat Model

| Threat | Control |
|---|---|
| Prompt injection in email | Email text never becomes application instructions |
| Malicious HTML/JavaScript | Structural inspection only; no browser execution |
| SSRF | No automatic URL fetcher; local/private destinations escalate |
| Dangerous attachment | Metadata-only inspection; no execution |
| Header spoofing | From/Reply-To/Return-Path/authentication indicators |
| Oversized input | Request/body/count limits |
| API key theft | Environment configuration, constant-time comparison, no logging |
| Secret leakage | Sanitized logging and Git exclusions |
| Priority bypass | Priority eligibility requires NON-PHISHING |
| Parser ambiguity | Fail-closed REVIEW REQUIRED |

Residual risks include no live URL reputation, no sandboxed attachment detonation, no production identity/rate limiting/managed secrets, and no externally verified deployment.
