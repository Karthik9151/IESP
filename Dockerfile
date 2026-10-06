FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app

COPY requirements-ml.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt -r requirements-api.txt

COPY backend ./backend
COPY src ./src
COPY configs ./configs
COPY models ./models
COPY data ./data

ARG IESP_MODEL_OWNER=Karthik9151
ARG IESP_MODEL_REPO=IESP
ARG IESP_MODEL_RELEASE_TAG=models-v1
ENV IESP_MODEL_OWNER=$IESP_MODEL_OWNER
ENV IESP_MODEL_REPO=$IESP_MODEL_REPO
ENV IESP_MODEL_RELEASE_TAG=$IESP_MODEL_RELEASE_TAG

RUN python - <<'PY'
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

owner = os.environ["IESP_MODEL_OWNER"]
repo = os.environ["IESP_MODEL_REPO"]
tag = os.environ["IESP_MODEL_RELEASE_TAG"]
base = f"https://github.com/{owner}/{repo}/releases/download/{tag}"

def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "IESP-model-fetch/1.0"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)

manifest_path = Path("/tmp/model-manifest.json")
download(f"{base}/model-manifest.json", manifest_path)
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

expected_fp = "34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582"
contract = manifest.get("m1_contract", {})
if contract.get("project_fingerprint") != expected_fp:
    raise SystemExit("M1 fingerprint mismatch in model release")
if (
    contract.get("train_records"),
    contract.get("validation_records"),
    contract.get("test_records"),
) != (76069, 16300, 16301):
    raise SystemExit("M1 split-size mismatch in model release")

targets = {
    "phishing": Path("/app/models/phishing"),
    "priority": Path("/app/models/priority"),
}
for name, directory in targets.items():
    info = manifest["models"][name]
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / info["filename"]
    download(f"{base}/{info['filename']}", destination)

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != info["sha256"]:
        raise SystemExit(f"SHA-256 mismatch for {destination}")
    if destination.stat().st_size != info["size_bytes"]:
        raise SystemExit(f"Size mismatch for {destination}")

print("IESP model artifacts verified successfully.")
PY

RUN useradd --create-home --shell /usr/sbin/nologin iesp && chown -R iesp:iesp /app
USER iesp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
