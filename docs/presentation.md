# IESP Product Demonstration Flow

## 1. Problem

Email security is not only about phishing classification. A useful security platform must inspect untrusted headers, URLs, HTML, and attachments safely while giving analysts understandable reasons for the decision.

## 2. Solution

IESP combines deterministic security analysis, phishing ML evidence, policy decisioning, priority scoring only for eligible non-phishing mail, and authenticated persistence/reporting.

```text
Security decision first
    ↓
PHISHING / SUSPICIOUS / REVIEW REQUIRED / NON-PHISHING
    ↓
Priority only when NON-PHISHING
    ↓
P1 / P2 / P3
```

## 3. Architecture

```text
Manual email / Gmail / Microsoft
            ↓
Safe parsing + normalization
            ↓
Security feature extraction
            ↓
TF-IDF + LinearSVC phishing evidence
            ↓
Security policy decision
            ↓
Priority eligibility
            ↓
FastAPI + PostgreSQL
            ↓
React dashboard
```

Email content is treated as untrusted data. HTML is analyzed structurally and is not rendered as trusted DOM; URLs are inspected without automatic network fetching; attachments are metadata-only.

## 4. Application workflow

1. Open `https://iesp-frontend.onrender.com`.
2. Register or log in.
3. Open Analyze.
4. Upload the prepared `.eml` sample.
5. Review Security verdict.
6. Review Policy risk score and distinguish it from ML probability.
7. Review Model decision margin and explain that LinearSVC output is a ranking margin, not a calibrated probability.
8. Review Security reasons, Priority assessment, Model metadata, Analysis time, and Request ID.
9. Open History and Reports.
10. Open Settings and verify Logout.

## 5. Security demonstration

Use a suspicious/phishing-style sample containing an urgency cue and a URL. Explain the resulting security reasons and show that priority is withheld when the final decision is PHISHING, SUSPICIOUS, or REVIEW REQUIRED.

Do not claim that the application performs live URL reputation checks, attachment detonation, or browser execution of email HTML.

## 6. OAuth integration

Gmail and Microsoft provider routes, state binding, PKCE, encrypted provider-token storage, and read-only adapters are implemented. Live provider consent requires valid provider-console credentials and matching redirect URIs, so demonstrate a real provider connection only when that environment has been configured and tested.

## 7. Testing and deployment

Mention the repository CI gates: backend/security tests, frontend tests/build, dependency audits, secret scanning, API contract validation, PostgreSQL integration, and Docker verification.

Render hosts the backend, frontend, and PostgreSQL resources from the repository deployment configuration.

## 8. Limitations and future work

- live URL reputation and network detonation are outside the current safe analysis boundary
- attachments are metadata-only
- P1/P2/P3 are proxy labels, not human-annotated urgency
- distributed rate limiting and production observability require further infrastructure
- live Gmail/Microsoft consent depends on external provider configuration

## One-line explanation

> IESP is a security-first email analysis platform that combines deterministic security rules with phishing ML evidence, persists explainable results, and deliberately prevents untrusted email content from becoming executable application content.
