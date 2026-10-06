from __future__ import annotations

from datetime import datetime

import httpx

from src.domain.models import AttachmentMetadata
from .base import ProviderError, ProviderMessageRef
from .normalizer import normalize_generic_message


class OutlookAdapter:
    """Read-only Microsoft Graph adapter using delegated Mail.Read."""

    name = "outlook"
    BASE_URL = "https://graph.microsoft.com/v1.0"
    READ_SCOPE = "Mail.Read"

    def __init__(self, access_token: str, *, timeout: float = 10.0, transport: httpx.BaseTransport | None = None):
        if not access_token:
            raise ValueError("Microsoft Graph access token is required")
        self._client = httpx.Client(base_url=self.BASE_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.get(path, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderError("Microsoft Graph request failed") from exc
        if response.status_code >= 400:
            raise ProviderError(f"Microsoft Graph returned HTTP {response.status_code}")
        return response

    def list_message_ids(self, *, limit: int = 20) -> list[ProviderMessageRef]:
        limit = max(1, min(limit, 100))
        data = self._get("/me/messages", params={"$top": limit, "$select": "id"}).json()
        return [ProviderMessageRef(self.name, item["id"]) for item in data.get("value", [])[:limit]]

    def fetch_message(self, message_id: str):
        data = self._get(f"/me/messages/{message_id}", params={"$select": "id,subject,body,from,toRecipients,ccRecipients,internetMessageHeaders,receivedDateTime"}).json()
        sender = ((data.get("from") or {}).get("emailAddress") or {})
        recipients = [i.get("emailAddress", {}).get("address", "") for i in (data.get("toRecipients") or []) + (data.get("ccRecipients") or []) if i.get("emailAddress", {}).get("address")]
        body = data.get("body") or {}
        headers = {h.get("name", "").lower(): h.get("value", "") for h in data.get("internetMessageHeaders") or [] if h.get("name")}
        received = data.get("receivedDateTime")
        received_at = datetime.fromisoformat(received.replace("Z", "+00:00")) if received else None
        return normalize_generic_message(
            message_id=data.get("id", message_id),
            sender_address=sender.get("address", ""),
            sender_name=sender.get("name", ""),
            recipients=recipients,
            subject=data.get("subject", ""),
            text_body=body.get("content", "") if body.get("contentType") == "text" else "",
            html_body=body.get("content", "") if body.get("contentType") == "html" else "",
            headers=headers,
            received_at=received_at,
        )

    def fetch_attachment_metadata(self, message_id: str) -> tuple[AttachmentMetadata, ...]:
        data = self._get(f"/me/messages/{message_id}/attachments", params={"$select": "name,contentType,size,isInline"}).json()
        return tuple(
            AttachmentMetadata(filename=i.get("name") or "unnamed", content_type=i.get("contentType") or "application/octet-stream", size_bytes=i.get("size"), disposition="inline" if i.get("isInline") else "attachment")
            for i in data.get("value", [])
        )

    def analyze_message(self, message_id: str, engine, *, request_id: str | None = None):
        message = self.fetch_message(message_id)
        return engine.analyze(message.__class__(**{**message.__dict__, "attachments": self.fetch_attachment_metadata(message_id)}), request_id=request_id)
