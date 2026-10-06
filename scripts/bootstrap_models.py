"""Bootstrap verified IESP ML model artifacts before starting the API."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_PROJECT = "IESP"
EXPECTED_FINGERPRINT = "34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582"
EXPECTED_SPLITS = (76069, 16300, 16301)
MODEL_DIRS = {
    "phishing": "phishing",
    "priority": "priority",
}


def _base_url() -> str:
    owner = os.getenv("IESP_MODEL_OWNER", "Karthik9151")
    repo = os.getenv("IESP_MODEL_REPO", "IESP")
    tag = os.getenv("IESP_MODEL_RELEASE_TAG", "models-v1")
    return f"https://github.com/{owner}/{repo}/releases/download/{tag}"


def _download(url: str, destination: Path) -> None:
    retries = max(1, int(os.getenv("IESP_MODEL_FETCH_RETRIES", "3")))
    delay = max(1, int(os.getenv("IESP_MODEL_FETCH_RETRY_DELAY", "5")))
    last_error: Exception | None = None
    destination.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, retries + 1):
        temporary: Path | None = None
        try:
            request = Request(url, headers={"User-Agent": "IESP-model-bootstrap/1.0"})
            with urlopen(request, timeout=120) as response, tempfile.NamedTemporaryFile(
                mode="wb",
                delete=False,
                dir=str(destination.parent),
                prefix=f".{destination.name}.",
            ) as output:
                temporary = Path(output.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            os.replace(temporary, destination)
            return
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            last_error = exc
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if attempt < retries:
                print(
                    f"Model download attempt {attempt}/{retries} failed: {exc}; retrying...",
                    flush=True,
                )
                time.sleep(delay)

    raise RuntimeError(f"Unable to download IESP model asset from {url}: {last_error}") from last_error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest(manifest: dict, expected_tag: str) -> None:
    if manifest.get("project") != EXPECTED_PROJECT:
        raise RuntimeError("Model release project marker is not IESP")
    if manifest.get("release_tag") != expected_tag:
        raise RuntimeError("Model release tag mismatch")

    contract = manifest.get("m1_contract")
    if not isinstance(contract, dict):
        raise RuntimeError("Model release is missing m1_contract")
    if contract.get("project_fingerprint") != EXPECTED_FINGERPRINT:
        raise RuntimeError("M1 fingerprint mismatch in model release")

    splits = (
        contract.get("train_records"),
        contract.get("validation_records"),
        contract.get("test_records"),
    )
    if splits != EXPECTED_SPLITS:
        raise RuntimeError(f"M1 split-size mismatch in model release: {splits}")

    models = manifest.get("models")
    if not isinstance(models, dict):
        raise RuntimeError("Model release is missing models")

    for name in MODEL_DIRS:
        info = models.get(name)
        if not isinstance(info, dict):
            raise RuntimeError(f"Model release is missing {name} model metadata")
        filename = info.get("filename")
        digest = info.get("sha256")
        size = info.get("size_bytes")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise RuntimeError(f"Invalid filename in {name} model metadata")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RuntimeError(f"Invalid SHA-256 in {name} model metadata")
        if not isinstance(size, int) or size <= 0:
            raise RuntimeError(f"Invalid size in {name} model metadata")


def _verify_artifact(path: Path, info: dict) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == int(info["size_bytes"])
        and _sha256(path) == info["sha256"]
    )


def _load_or_fetch_manifest(models_root: Path) -> dict:
    tag = os.getenv("IESP_MODEL_RELEASE_TAG", "models-v1")
    manifest_path = models_root / "model-manifest.json"

    try:
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            _validate_manifest(manifest, tag)
            return manifest
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Cached model manifest is invalid; refreshing: {exc}", flush=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=str(models_root),
        prefix=".model-manifest.",
        suffix=".json",
    ) as output:
        temporary = Path(output.name)

    try:
        _download(f"{_base_url()}/model-manifest.json", temporary)
        manifest = json.loads(temporary.read_text(encoding="utf-8"))
        _validate_manifest(manifest, tag)
        os.replace(temporary, manifest_path)
        return manifest
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def bootstrap(models_root: Path) -> None:
    models_root.mkdir(parents=True, exist_ok=True)
    manifest = _load_or_fetch_manifest(models_root)
    base = _base_url()

    for name, directory_name in MODEL_DIRS.items():
        info = manifest["models"][name]
        destination = models_root / directory_name / info["filename"]

        if _verify_artifact(destination, info):
            print(f"Verified existing {name} model artifact: {destination}", flush=True)
            continue

        if destination.exists():
            print(f"Replacing invalid {name} model artifact: {destination}", flush=True)
            destination.unlink()

        _download(f"{base}/{info['filename']}", destination)
        if not _verify_artifact(destination, info):
            destination.unlink(missing_ok=True)
            raise RuntimeError(
                f"Downloaded {name} model artifact failed SHA-256/size verification"
            )
        print(f"Downloaded and verified {name} model artifact: {destination}", flush=True)


def main() -> int:
    models_root = Path(os.getenv("IESP_MODEL_ROOT", "/app/models"))

    try:
        bootstrap(models_root)
    except Exception as exc:
        print(f"IESP model bootstrap failed: {exc}", file=sys.stderr, flush=True)
        return 1

    command = sys.argv[1:]
    if not command:
        command = [
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]

    os.execvp(command[0], command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
