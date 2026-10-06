# IESP

## Intelligent Email Security & Prioritization System

IESP is a production-oriented academic prototype combining NLP, machine learning, cybersecurity analysis, and real-time email integration.

### Core decision flow

Email -> Security analysis -> Security decision -> Priority analysis for eligible non-phishing email -> P1/P2/P3

Security evaluation always happens before priority classification.

### Current status

**Milestone 0 — Repository audit and architecture**

The repository foundation and architecture are being established. The ML models, enhanced security engine implementation, API, frontend, mail integrations, testing, CI/CD, and deployment are intentionally deferred to their later milestones.

### Documentation

- docs/current-state.md
- docs/architecture.md
- docs/implementation-plan.md
- docs/threat-model.md
- docs/ml-methodology.md
- docs/mail-integrations.md
- docs/deployment.md
- docs/limitations.md

### Research integrity

The supplied report contains conflicting dataset counts (900 emails versus 5,572 rows reduced to 5,169 unique records). This must be verified against the authoritative dataset in Milestone 1.

Historical accuracy figures are not treated as reproduced results without independently matching the data, preprocessing, split, and implementation.
