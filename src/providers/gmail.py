from __future__ import annotations

import base64

import httpx

from src.parsing.email_parser import parse_email_bytes
from .base import ProviderError, ProviderMessageRef


class GmailAdapter:
    """Read-only Gmail adapter; uses gmail.readonly and never mutates mailbox state."""

    name = "gmail"
    BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
    READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

    def __init__(self, access_token: str, *, timeout: float = 10.0, transport: httpx.BaseTransport | None = None):
        if not access_token:
            raise ValueError("Gmail access token is required")
        self._client = httpx.Client(base_url=self.BASE_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.get(path, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderError("Gmail request failed") from exc
        if response.status_code >= 400:
            raise ProviderError(f"Gmail returned HTTP {response.status_code}")
        return response

    def list_message_ids(self, *, limit: int = 20) -> list[ProviderMessageRef]:
        limit = max(1, min(limit, 100))
        data = self._get("/messages", params={"maxResults": limit}).json()
        return [ProviderMessageRef(self.name, item["id"]) for item in data.get("messages", [])[:limit]]

    def fetch_message(self, message_id: str):
        data = self._get(f"/messages/{message_id}", params={"format": "raw"}).json()
        raw = data.get("raw")
        if not raw:
            raise ProviderError("Gmail message did not contain raw MIME data")
        try:
            decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
            return parse_email_bytes(decoded)
        except Exception as exc:
            raise ProviderError("Gmail message could not be parsed safely") from exc

    def analyze_message(self, message_id: str, engine, *, request_id: str | None = None):
        return engine.analyze(self.fetch_message(message_id), request_id=request_id)
