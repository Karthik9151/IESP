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

## Model release

The production backend requires both ML runtime artifacts.

`.github/workflows/build-model-release.yml` downloads the authoritative MeAJOR release from Zenodo, verifies its checksum and accepted M1 contract, trains both models, verifies the artifacts, and publishes them to the public GitHub Release `models-v1`.

The authoritative model-release workflow **#16** completed successfully from commit `1b84ff5f2a8d33b22cab6294b085d97e8964cb21`.

The workflow remains manually runnable and also runs automatically on `main` when the model-building workflow, M1 pipeline, ML code/configuration, or ML dependencies change.

The dataset itself is never committed to GitHub.

## Docker

The Docker image no longer downloads model artifacts during `docker build`. This keeps image construction independent from the availability of the external model release.

At container startup, `scripts/bootstrap_models.py` downloads `models-v1` when required, validates the release manifest, checks the accepted M1 fingerprint/split contract, verifies SHA-256 and file size for both artifacts, and then starts the API. Existing valid artifacts are reused.

```bash
docker build -t iesp-backend .
docker run --rm -p 8000:8000 \
  -e IESP_ENVIRONMENT=development \
  -e IESP_AUTH_MODE=disabled \
  iesp-backend
```

If `models-v1` does not yet exist, the image can still be built, but the container will not start until the release is published.

## Render

The recommended production/demo layout is two Render services:

1. Backend: Render Web Service using the repository Dockerfile.
2. Frontend: Render Static Site built from `frontend/`.

The backend Docker runtime honors Render's `PORT` environment variable and starts on `0.0.0.0`. The startup bootstrap downloads `models-v1`, validates the M1 contract, and verifies SHA-256 and file sizes before the API starts.

Backend settings:

- Runtime: Docker
- Root directory: repository root
- Health check path: `/ready`
- `IESP_ENVIRONMENT=production`
- `IESP_AUTH_MODE=required`
- `IESP_API_KEY`: set as a Render secret
- `IESP_ALLOWED_ORIGINS`: set to the exact deployed frontend origin
- `IESP_DATABASE_PATH=/app/data/iesp.sqlite3`
- `IESP_MODEL_RELEASE_TAG=models-v1`

Frontend settings:

- Service type: Static Site
- Root directory: `frontend`
- Build command: `npm install --no-audit --no-fund && npm run build`
- Publish directory: `dist`
- `VITE_API_BASE_URL`: exact HTTPS URL of the deployed backend

After deployment, verify:

- backend `/health` -> HTTP 200
- backend `/ready` -> HTTP 200 with `{"status":"ready","blockers":[]}`
- frontend loads over HTTPS
- browser requests from the frontend to `/api/v1/stats` and `/api/v1/analyze` succeed with the backend API key
- a test analysis is persisted and then visible through the recent/history endpoint

The deployed service should not be considered ready until the `/ready` response is observed.

Render's free web services have ephemeral filesystems, so the project's SQLite history is not durable across deploys, restarts, or free-instance spin-down. Use Render Postgres or another durable datastore when persistent production history is required.

## CI

GitHub Actions performs Python compilation/tests, frontend tests/build, dependency auditing and secret scanning. CI #48 is the current green baseline.

## Free-hosting limitation

Render's free filesystem is ephemeral, so SQLite data is not durable across restarts/redeploys. A managed persistent database is required for durable production history.

## Status

Model-release automation is **VERIFIED** by workflow #16. External deployment remains **PENDING** until Render health/readiness is actually observed to succeed.
