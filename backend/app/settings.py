from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    environment: str = field(default_factory=lambda: os.getenv("IESP_ENVIRONMENT","development").lower())
    allowed_origins: tuple[str,...] = field(default_factory=lambda: tuple(x.strip().rstrip("/") for x in os.getenv("IESP_ALLOWED_ORIGINS","http://localhost:5173").split(",") if x.strip()))
    session_cookie_name: str = field(default_factory=lambda: os.getenv("IESP_SESSION_COOKIE","iesp_session"))
    session_cookie_secure: bool = field(default_factory=lambda: os.getenv("IESP_SESSION_SECURE","false").lower()=="true")
    session_cookie_samesite: str = field(default_factory=lambda: os.getenv("IESP_SESSION_SAMESITE","lax").lower())
    session_ttl_hours: int = field(default_factory=lambda: int(os.getenv("IESP_SESSION_TTL_HOURS","12")))
    max_request_bytes: int = field(default_factory=lambda: int(os.getenv("IESP_MAX_REQUEST_BYTES","2500000")))
    max_email_bytes: int = field(default_factory=lambda: int(os.getenv("IESP_MAX_EMAIL_BYTES","2000000")))
    analysis_rate_limit: int = field(default_factory=lambda: int(os.getenv("IESP_ANALYSIS_RATE_LIMIT","20")))
    analysis_rate_window_seconds: int = field(default_factory=lambda: int(os.getenv("IESP_ANALYSIS_RATE_WINDOW","60")))
    high_risk_threshold: float = field(default_factory=lambda: float(os.getenv("IESP_HIGH_RISK_THRESHOLD","75")))
    history_page_size: int = field(default_factory=lambda: int(os.getenv("IESP_HISTORY_PAGE_SIZE","25")))
    report_export_limit: int = field(default_factory=lambda: int(os.getenv("IESP_REPORT_EXPORT_LIMIT","5000")))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL",""))
    database_path: Path = field(default_factory=lambda: Path(os.getenv("IESP_DATABASE_PATH","data/iesp.sqlite3")))
    security_config: Path = field(default_factory=lambda: Path(os.getenv("IESP_SECURITY_CONFIG","configs/security.yaml")))
    phishing_artifact: Path = field(default_factory=lambda: Path(os.getenv("IESP_PHISHING_ARTIFACT","models/phishing/phishing_pipeline.joblib")))
    priority_artifact: Path = field(default_factory=lambda: Path(os.getenv("IESP_PRIORITY_ARTIFACT","models/priority/priority_pipeline.joblib")))
    model_version: str = field(default_factory=lambda: os.getenv("IESP_MODEL_VERSION","models-v1"))
    policy_version: str = field(default_factory=lambda: os.getenv("IESP_POLICY_VERSION","policy-v1"))

    def validate(self)->None:
        if self.environment not in {"development","test","production"}: raise ValueError("IESP_ENVIRONMENT must be development, test, or production")
        if self.session_cookie_samesite not in {"lax","strict","none"}: raise ValueError("IESP_SESSION_SAMESITE must be lax, strict, or none")
        if self.session_cookie_samesite=="none" and not self.session_cookie_secure: raise ValueError("SameSite=None requires a secure session cookie")
        if self.session_ttl_hours<=0: raise ValueError("IESP_SESSION_TTL_HOURS must be positive")
        if self.max_request_bytes<=0 or self.max_email_bytes<=0 or self.max_email_bytes>self.max_request_bytes: raise ValueError("Request/email size limits are invalid")
        if self.analysis_rate_limit<=0 or self.analysis_rate_window_seconds<=0: raise ValueError("Analysis rate limiting must be positive")
        if not 0<=self.high_risk_threshold<=100: raise ValueError("High-risk threshold must be between 0 and 100")
        if not 1<=self.history_page_size<=100 or not 1<=self.report_export_limit<=50000: raise ValueError("History/report limits are invalid")
        if self.environment=="production" and not self.database_url.startswith(("postgres://","postgresql://")): raise ValueError("Production requires PostgreSQL DATABASE_URL")
        if self.environment=="production" and not self.session_cookie_secure: raise ValueError("Production requires a secure session cookie")
        if self.environment=="production" and (not self.allowed_origins or "*" in self.allowed_origins): raise ValueError("Production requires explicit CORS origins")
