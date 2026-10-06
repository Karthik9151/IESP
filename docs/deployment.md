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

Use the manual GitHub Actions workflow:

`.github/workflows/build-model-release.yml`

It downloads the authoritative MeAJOR release from Zenodo, verifies its checksum and accepted M1 contract, trains both models, verifies the artifacts, and publishes them to the public GitHub Release `models-v1`.

The dataset itself is never committed to GitHub.

## Docker

After the `models-v1` release exists:

```bash
docker build -t iesp-backend .
docker run --rm -p 8000:8000 \
  -e IESP_ENVIRONMENT=development \
  -e IESP_AUTH_MODE=disabled \
  iesp-backend
```

The Docker build downloads the two model artifacts from the pinned release tag and verifies SHA-256 plus the accepted M1 fingerprint/split contract.

## Render

The Render backend service uses the repository Dockerfile. Once `models-v1` has been published, trigger a new Render deploy from the `main` branch.

After deployment, verify:

- `/health` → `{"status":"ok"}`
- `/ready` → `{"status":"ready","blockers":[]}`

The deployed service should not be considered ready until the second response is observed.

## CI

GitHub Actions performs Python compilation/tests, frontend tests/build, dependency auditing and secret scanning.

## Free-hosting limitation

Render's free filesystem is ephemeral, so SQLite data is not durable across restarts/redeploys. A managed persistent database is required for durable production history.

## Status

Model-release automation is IMPLEMENTED. External deployment remains PENDING until the model-release workflow and Render rebuild are actually observed to succeed.
