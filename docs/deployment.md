# Deployment

## Local

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt -r requirements-api.txt
export IESP_ENVIRONMENT=development
uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

The browser authenticates using an HTTP-only session cookie. No API key is needed in frontend code.

## Model release

The production backend requires the existing `models-v1` runtime artifacts. The startup bootstrap downloads and verifies the release manifest, accepted M1 fingerprint/split contract, artifact size and SHA-256 before starting the API.

The authoritative dataset remains outside Git.

## Docker

The backend image runs as an unprivileged `iesp` user and verifies model artifacts at container startup.

```bash
docker build -t iesp-backend .
docker run --rm -p 8000:8000 \
  -e IESP_ENVIRONMENT=development \
  iesp-backend
```

For local persistent history, mount `/app/data`. Production should use PostgreSQL for durable history.

The frontend Docker image builds the Vite application and serves static assets with Nginx security headers.

## Render

The repository Blueprint defines:

1. Backend: Render Web Service using the repository Dockerfile.
2. Database: Render Postgres.
3. Frontend: Render Static Site from `frontend/dist`.

Production backend settings include:

- `IESP_ENVIRONMENT=production`
- `DATABASE_URL` from Render Postgres
- `IESP_SESSION_SECURE=true`
- `IESP_SESSION_SAMESITE=none`
- exact HTTPS CORS origin wiring from the frontend service
- bounded request/email limits
- existing security/model configuration paths

No API key is placed in frontend build variables or browser storage. `VITE_API_BASE_URL` is public configuration only.

Current production frontend:
- service display name: `iesp-home`
- Render-managed URL: `https://iesp-frontend.onrender.com`

The existing Render subdomain name does not need to match the service display name for the application to work.

## CI

GitHub Actions provides blocking gates for Python compilation/full tests, dependency consistency + `pip-audit`, frontend tests/build, `npm audit`, repository+history secret scanning, OpenAPI contract smoke validation, PostgreSQL integration, and Docker image builds. Frontend and Render builds use the committed `frontend/package-lock.json` with `npm ci`.

## External verification

Only claim production browser/API or live provider OAuth success after observing it in the real deployed/provider environment and recording the result.