from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("IESP_ENVIRONMENT", "development").lower()
    auth_mode: str = os.getenv("IESP_AUTH_MODE", "required").lower()
    api_key: str = os.getenv("IESP_API_KEY", "")
    allowed_origins: tuple[str, ...] = tuple(x.strip() for x in os.getenv("IESP_ALLOWED_ORIGINS", "").split(",") if x.strip())
    max_request_bytes: int = int(os.getenv("IESP_MAX_REQUEST_BYTES", str(1024 * 1024)))
    security_config: Path = Path(os.getenv("IESP_SECURITY_CONFIG", "configs/security.yaml"))
    phishing_artifact: Path = Path(os.getenv("IESP_PHISHING_ARTIFACT", "models/phishing/phishing_pipeline.joblib"))
    priority_artifact: Path = Path(os.getenv("IESP_PRIORITY_ARTIFACT", "models/priority/priority_pipeline.joblib"))

    def validate(self) -> None:
        if self.auth_mode not in {"required", "disabled"}:
            raise ValueError("IESP_AUTH_MODE must be required or disabled")
        if self.auth_mode == "disabled" and self.environment not in {"development", "test"}:
            raise ValueError("Authentication can only be disabled in development/test")
        if self.auth_mode == "required" and not self.api_key:
            raise ValueError("IESP_API_KEY must be configured when authentication is required")
        if self.max_request_bytes <= 0:
            raise ValueError("IESP_MAX_REQUEST_BYTES must be positive")
