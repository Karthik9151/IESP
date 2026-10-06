# Current Repository State

**Audit date:** 2026-10-06  
**Repository:** Karthik9151/IESP  
**Default branch:** main  
**Development branch:** milestone-0-architecture

## Repository inventory

The current main branch contains the following foundation:

.
├── README.md
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── .gitkeep
├── app/
│   └── .gitkeep
├── data/
│   └── .gitkeep
├── docs/
│   ├── architecture.md
│   ├── current-state.md
│   ├── deployment.md
│   ├── implementation-plan.md
│   ├── limitations.md
│   ├── mail-integrations.md
│   ├── ml-methodology.md
│   └── threat-model.md
├── frontend/
│   └── .gitkeep
├── models/
│   └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
└── tests/
    └── .gitkeep

## Existing functionality

No application implementation is currently present.

| Area | Current state |
|---|---|
| FastAPI backend | Not implemented |
| React/Vite frontend | Not implemented |
| NLP/ML training | Not implemented |
| Phishing SVM | Not implemented |
| Priority Logistic Regression | Not implemented |
| Enhanced security engine | Not implemented |
| Gmail integration | Not implemented |
| Microsoft Graph integration | Not implemented |
| Generic IMAP integration | Not implemented |
| Database | Not implemented |
| Docker | Not implemented |
| GitHub Actions CI | Placeholder only |
| Automated tests | Placeholder only |
| Authoritative dataset | Not present in repository |
| Model artifacts | Not present |

## Existing documentation

The architecture, implementation plan, threat model, ML methodology, mail integration plan, deployment plan, and limitations documents provide the intended Milestone 0 design and later execution contract.

## Important audit findings

### 1. Dataset ambiguity

The project specification contains conflicting dataset descriptions:

- 900 emails in one section.
- 5,572 rows reduced to 5,169 unique records in another.

No dataset count is assumed to be correct. Milestone 1 must identify the authoritative source and measure the actual rows, duplicates, labels, and provenance.

### 2. Research integrity

The historical model metrics in the supplied report are not automatically reproduced results.

A metric can only be reported as reproduced when the exact dataset, labels, preprocessing, split, parameters, and evaluation procedure are verified.

### 3. Security ordering

The architecture requires:

Security analysis -> security decision -> priority classification only for eligible non-phishing messages.

### 4. Untrusted email data

Email body text, HTML, URLs, headers, and attachment metadata must be treated as untrusted input. They must never become application instructions.

## Milestone 0 acceptance status

- [x] Repository audited
- [x] Current state documented
- [x] Architecture documented
- [x] Milestone plan documented
- [x] Threat model documented
- [x] ML methodology documented
- [x] Mail integration architecture documented
- [x] Deployment/limitations documented
- [x] Dataset inconsistency documented
- [x] No ML/backend/frontend/mail implementation started

Milestone 1 is intentionally blocked until explicitly authorized after review.
