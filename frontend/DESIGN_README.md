# IESP — Cyber Defence Command Centre UI

The React dashboard provides the operator-facing security workspace without changing the FastAPI routes, PostgreSQL behavior, session-cookie authentication, or provider OAuth contracts.

## Run

```bash
cd frontend
npm ci
npm run dev
```

## Design system

Dark mode is the default.

- Background: `#0A0F1C`
- Surface: `#111827`
- Raised surface: `#172036`
- Border: `#243049`
- Defence accent: `#22D3EE`
- PHISHING: `#EF4444`
- SUSPICIOUS: `#F59E0B`
- REVIEW REQUIRED: `#8B5CF6`
- NON-PHISHING: `#10B981`
- Text: `#E5E7EB`
- Secondary text: `#94A3B8`

Inter is used for UI copy; IBM Plex Mono is used for message IDs, sender addresses, and safe email content.

## Verdict and priority rules

Every verdict includes both an icon and a text label.

Priority P1/P2/P3 is displayed only when the API returns a priority for a NON-PHISHING result. All other verdicts show:

> Priority withheld – security review first

The UI explicitly describes P1/P2/P3 as proxy labels rather than human-annotated urgency.

## Safe email presentation

Email HTML is never rendered into the DOM. Live analysis results can show a local safe preview of the submitted message as inert plain text. URLs are defanged and not clickable, and attachment metadata is marked NEVER EXECUTED.

The existing stored-analysis API does not persist raw message bodies, so History detail truthfully shows that the original body is not available there.

## Accessibility checklist

- Semantic landmarks and labelled sections
- Keyboard-visible focus rings
- Minimum 44px primary touch targets
- Verdicts are distinguishable by icon + text, not colour alone
- ARIA labels on charts and live analysis states
- Keyboard shortcuts: `/`, `g d`, `g a`, `g h`, `g r`, `g s`, `?`
- `prefers-reduced-motion` support
- Mobile layouts from approximately 360px through desktop widths
- Inline upload validation for extension and 2MB limit
- Confirmation before logout/disconnect actions

## Truthfulness

Dashboard/report numbers come from existing API responses. The UI does not invent accuracy, F1, ROC-AUC, provider-success, or deployment-success figures. The activity chart is intentionally limited to the latest records available from the existing API.
