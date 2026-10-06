# IESP Presentation / Demo Flow

1. Problem — phishing, malicious links/attachments and email volume.
2. Solution — security-first classification followed by priority only for eligible non-phishing mail.
3. Architecture — provider → safe parsing → security features → phishing ML → decision → priority → FastAPI → React.
4. Dataset/ML — accepted M1 fingerprint/splits; TF-IDF + LinearSVC; VADER/features + LogisticRegression; proxy-label limitation.
5. Security demo — normal message, hostile URL/header/attachment, malformed MIME or local/private destination.
6. API demo — `/health`, `/ready`, authenticated `/api/v1/analyze`; show priority suppression.
7. Dashboard demo — statistics, manual analysis, reason codes and audit metadata.
8. Provider demo — mocked Gmail/Graph adapter tests; live OAuth explicitly marked untested.
9. Testing/deployment — pytest, frontend test/build, CI, secret scan, Docker/Compose configuration.
10. Limitations/future work — managed identity/OAuth, sandboxing, vetted URL reputation, human urgency labels, production persistence, rate limiting, observability and deployment.
