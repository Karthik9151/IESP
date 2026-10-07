# Mail Integrations

Provider code is isolated from the IESP engine. Each adapter produces the shared `EmailMessage` model and uses the same security pipeline.

## Gmail

Read-only Gmail adapter using `gmail.readonly`. Raw MIME is retrieved and passed to the safe parser. The adapter exposes retrieval/analysis only and never mutates mailbox state.

## Microsoft Graph

Read-only Graph adapter using `Mail.Read`. Messages and attachment metadata are normalized without executing or detonation of content. No mailbox mutation method is exposed.

## OAuth

Helpers create unpredictable state values, validate callback state with constant-time comparison, and create PKCE verifier/challenge values. The authorization URL builder can now include the PKCE S256 challenge. Access tokens must come from secure server-side/external credential management.

The repository currently does not expose application-level provider OAuth start/callback routes or a provider-token lifecycle. Therefore live Gmail/Microsoft OAuth cannot yet be run through the IESP application.

## Status

Mocked HTTP transport tests cover adapter retrieval, normalization and provider failures, plus OAuth state/PKCE helper behavior. Live OAuth consent, callback/token exchange, mailbox retrieval and end-to-end analysis remain NOT VERIFIED pending an application-level OAuth flow and user-owned provider configuration.