# Mail Integrations

Provider code is isolated from the IESP engine. Each adapter produces the shared `EmailMessage` model and uses the same security pipeline.

## Gmail

Read-only Gmail adapter using `gmail.readonly`. Raw MIME is retrieved and passed to the safe parser. The adapter exposes retrieval/analysis only and never mutates mailbox state.

## Microsoft Graph

Read-only Graph adapter using `Mail.Read`. Messages and attachment metadata are normalized without executing or detonation of content. No mailbox mutation method is exposed.

## OAuth

Helpers create unpredictable state values, validate callback state with constant-time comparison, and create PKCE verifier/challenge values. Access tokens must come from an external credential manager.

## Status

Mocked HTTP transport tests cover successful retrieval, normalization and provider failures. Live OAuth consent and mailbox validation are PENDING because they require user-owned application registrations and credentials.
