from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class OAuthConfig:
    authorization_endpoint: str
    client_id: str
    redirect_uri: str
    scopes: tuple[str, ...]


def create_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorization_url(config: OAuthConfig, state: str) -> str:
    if not state or len(state) < 16:
        raise ValueError("OAuth state must be unpredictable and non-empty")
    return f"{config.authorization_endpoint}?{urlencode({'client_id': config.client_id, 'redirect_uri': config.redirect_uri, 'response_type': 'code', 'scope': ' '.join(config.scopes), 'state': state})}"


def validate_state(expected: str, received: str) -> bool:
    return bool(expected and received and hmac.compare_digest(expected, received))


def create_pkce_verifier() -> str:
    return secrets.token_urlsafe(48)


def create_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
