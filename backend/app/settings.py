from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str = field(default_factory=lambda: os.getenv("IESP_ENVIRONMENT", "development").lower())
    auth_mode: str = field(default_factory=lambda: os.getenv("IESP_AUTH_MODE", "required").lower())
    api_key: str = field(default_factory=lambda: os.getenv("IESP_API_KEY", ""))
    allowed_origins: tuple[str, ...] = field(default_factory=lambda: tuple(v.strip() for v in os.getenv("IESP_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if v.strip()))
    max_request_bytes: int = field(default_factory=lambda: int(os.getenv("IESP_MAX_REQUEST_BYTES", str(1024 * 1024))))
    security_config: Path = field(default_factory=lambda: Path(os.getenv("IESP_SECURITY_CONFIG", "configs/security.yaml")))
    phishing_artifact: Path = field(default_factory=lambda: Path(os.getenv("IESP_PHISHING_ARTIFACT", "models/phishing/phishing_pipeline.joblib")))
    priority_artifact: Path = field(default_factory=lambda: Path(os.getenv("IESP_PRIORITY_ARTIFACT", "models/priority/priority_pipeline.joblib")))
    database_path: Path = field(default_factory=lambda: Path(os.getenv("IESP_DATABASE_PATH", "data/iesp.sqlite3")))

    def validate(self) -> None:
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("IESP_ENVIRONMENT must be development, test, or production")
        if self.auth_mode not in {"required", "disabled"}:
            raise ValueError("IESP_AUTH_MODE must be required or disabled")
        if self.auth_mode == "disabled" and self.environment not in {"development", "test"}:
            raise ValueError("Authentication can only be disabled in development/test")
        if self.auth_mode == "required" and self.environment == "production" and not self.api_key:
            raise ValueError("IESP_API_KEY is required in production")
        if self.max_request_bytes <= 0:
            raise ValueError("IESP_MAX_REQUEST_BYTES must be positive")
        if any(origin == "*" for origin in self.allowed_origins):
            raise ValueError("Wildcard CORS origins are not permitted")
