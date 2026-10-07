from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    environment: str = field(default_factory=lambda: os.getenv('IESP_ENVIRONMENT','development').lower())
    allowed_origins: tuple[str,...] = field(default_factory=lambda: tuple(x.strip().rstrip('/') for x in os.getenv('IESP_ALLOWED_ORIGINS','http://localhost:5173').split(',') if x.strip()))
    session_cookie_name: str = field(default_factory=lambda: os.getenv('IESP_SESSION_COOKIE','iesp_session'))
    session_cookie_secure: bool = field(default_factory=lambda: os.getenv('IESP_SESSION_SECURE','false').lower()=='true')
    session_ttl_hours: int = field(default_factory=lambda: int(os.getenv('IESP_SESSION_TTL_HOURS','12')))
    max_request_bytes: int = field(default_factory=lambda: int(os.getenv('IESP_MAX_REQUEST_BYTES',str(2_500_000))))
    max_email_bytes: int = field(default_factory=lambda: int(os.getenv('IESP_MAX_EMAIL_BYTES',str(2_000_000))))
    analysis_rate_limit: int = field(default_factory=lambda: int(os.getenv('IESP_ANALYSIS_RATE_LIMIT','20')))
    analysis_rate_window_seconds: int = field(default_factory=lambda: int(os.getenv('IESP_ANALYSIS_RATE_WINDOW','60')))
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL',''))
    database_path: Path = field(default_factory=lambda: Path(os.getenv('IESP_DATABASE_PATH','data/iesp.sqlite3')))
    security_config: Path = field(default_factory=lambda: Path(os.getenv('IESP_SECURITY_CONFIG','configs/security.yaml')))
    phishing_artifact: Path = field(default_factory=lambda: Path(os.getenv('IESP_PHISHING_ARTIFACT','models/phishing/phishing_pipeline.joblib')))
    priority_artifact: Path = field(default_factory=lambda: Path(os.getenv('IESP_PRIORITY_ARTIFACT','models/priority/priority_pipeline.joblib')))
    def validate(self):
        if self.environment=='production' and not self.database_url.startswith(('postgres://','postgresql://')): raise ValueError('Production requires PostgreSQL DATABASE_URL.')
        if self.environment=='production' and not self.session_cookie_secure: raise ValueError('Production requires a secure session cookie.')
        if self.environment=='production' and (not self.allowed_origins or '*' in self.allowed_origins): raise ValueError('Production requires explicit CORS origins.')