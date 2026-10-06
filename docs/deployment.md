# Deployment

## Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt -r requirements-api.txt
export IESP_ENVIRONMENT=development
export IESP_API_KEY='replace-with-a-random-secret'
uvicorn backend.app.main:app --reload
```

Start the frontend with `cd frontend && npm install && npm run dev`.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend listens on port 8000 and frontend on 8080. Runtime model/data directories are mounted separately.

## CI

GitHub Actions performs Python compilation/tests, frontend tests/build, dependency auditing and secret scanning.

## Production

Add TLS, external secret management, server-side identity/session handling, rate limiting, managed persistent storage, monitoring, restricted network egress, vulnerability scanning and rollback procedures.

## Status

Docker/Compose and CI configuration are IMPLEMENTED. Local Docker execution and external hosting deployment are PENDING because those environments were not available for verification.
