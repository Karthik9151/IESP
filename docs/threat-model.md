# IESP Security Threat Model — Milestones 4–5

## Security objective

Treat email content and metadata as untrusted input. Security classification is authoritative and always precedes priority classification.

## Implemented security indicators

Header analysis checks From/Return-Path mismatch, From/Reply-To mismatch, authentication-result SPF/DKIM/DMARC failure indicators, and Received-SPF failure when present.

URL analysis is structural only. It checks scheme, hostname, port, userinfo, IP-literal hosts, local/non-public destinations, punycode, excessive subdomains, shortened hosts, suspicious encoding, URL length and URL count. No URL is fetched automatically.

Attachment analysis is metadata-only. It checks filename/extension, dangerous executable or script extensions, double extensions, size and count limits, and filename/MIME mismatch. Attachments are never executed.

## Decision matrix

| Condition | Outcome |
|---|---|
| Parser failure or critical security signal | REVIEW REQUIRED |
| Strong phishing score plus configured supporting high-severity signal | PHISHING |
| Positive phishing evidence without enough support | SUSPICIOUS |
| Meaningful deterministic security signals | SUSPICIOUS |
| No meaningful concern with required phishing evidence | NON-PHISHING |
| Required phishing evidence unavailable | REVIEW REQUIRED |

Thresholds live in configs/security.yaml. They are engineering policy defaults and are not claimed as scientifically validated thresholds.

## SSRF policy

M4 makes no external network requests. Localhost, local names and non-public IP-literal destinations are escalated as SSRF-sensitive. Any future network capability must validate schemes, redirects and resolved destinations, reject loopback/private/link-local/metadata-service ranges, and use strict timeouts.

## Logging policy

Logs use request ID, message ID, decision, reason codes and timing. Full email bodies, raw attachments, passwords, API keys, access tokens, refresh tokens and credential-like values are excluded from default logging.

## API controls

M5 uses strict Pydantic models with forbidden extra fields, explicit input size/count limits, header validation, environment-provided API-key authentication with constant-time comparison, an authorization boundary, request IDs, safe structured errors, and restrictive CORS. Health is public; analysis requires authentication unless explicit development/test-only auth disabling is configured.

## Residual risks

The baseline does not provide live URL reputation, sandboxed attachment detonation, antivirus execution, genuine human priority annotation, mail-provider OAuth integration, production rate limiting, or production secret management. Those remain future hardening work.
