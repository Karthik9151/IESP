from __future__ import annotations
import hmac
from dataclasses import dataclass
from fastapi import Header, HTTPException, status
from .settings import Settings

@dataclass(frozen=True)
class AuthorizationContext:
    authenticated: bool
    role: str = "analysis"

def require_api_key(settings: Settings):
    async def dependency(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> AuthorizationContext:
        if settings.auth_mode == "disabled":
            if settings.environment not in {"development", "test"}:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": "AUTH_CONFIG_ERROR", "message": "Authentication configuration is invalid."})
            return AuthorizationContext(True)
        if not x_api_key or not settings.api_key or not hmac.compare_digest(x_api_key, settings.api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "AUTH_REQUIRED", "message": "Valid API key required."})
        return AuthorizationContext(True)

    return dependency

def authorize_analysis(context: AuthorizationContext) -> None:
    if not context.authenticated or context.role != "analysis":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN", "message": "Not authorized for analysis."})
