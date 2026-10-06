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

The Render backend service uses the repository Dockerfile. Build success no longer depends on the model release being present.

After `models-v1` is published, deploy/restart the backend so the startup bootstrap can download and verify the artifacts.

After deployment, verify:

- `/health` → `{"status":"ok"}`
- `/ready` → `{"status":"ready","blockers":[]}`

The deployed service should not be considered ready until the second response is observed.

## CI

GitHub Actions performs Python compilation/tests, frontend tests/build, dependency auditing and secret scanning.

## Free-hosting limitation

Render's free filesystem is ephemeral, so SQLite data is not durable across restarts/redeploys. A managed persistent database is required for durable production history.

## Status

Model-release automation is IMPLEMENTED. External deployment remains PENDING until the model-release workflow and Render readiness are actually observed to succeed.
