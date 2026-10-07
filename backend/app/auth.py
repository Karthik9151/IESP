from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyCookie


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    try:
        prefix, salt_hex, digest_hex = encoded.rsplit("$", 2)
        _, n, r, p = prefix.split("$")
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorizationContext:
    user_id: int
    workspace_id: int
    email: str
    role: str


def issue_session(repo, user_id: int, workspace_id: int, settings) -> str:
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    repo.create_session(token_hash(raw_token), user_id, workspace_id, expires_at)
    return raw_token


def clear_session(repo, token: str | None) -> None:
    if token:
        repo.delete_session(token_hash(token))


def require_session(repo, settings):
    cookie_scheme = APIKeyCookie(name=settings.session_cookie_name, scheme_name="IESPSessionCookie", auto_error=False)

    def dependency(request: Request, token: str | None = Security(cookie_scheme)) -> AuthorizationContext:
        if token is None:
            token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise HTTPException(401, detail={"code": "AUTH_REQUIRED", "message": "Authentication is required."})
        row = repo.get_session(token_hash(token))
        if not row:
            raise HTTPException(401, detail={"code": "SESSION_INVALID", "message": "Authentication is required."})
        return AuthorizationContext(
            user_id=int(row["user_id"]),
            workspace_id=int(row["workspace_id"]),
            email=str(row["email"]),
            role=str(row["role"]),
        )

    return dependency
