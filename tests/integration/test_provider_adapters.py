from __future__ import annotations

import base64
import httpx
import pytest

from src.providers.gmail import GmailAdapter
from src.providers.outlook import OutlookAdapter
from src.providers.oauth import OAuthConfig, build_authorization_url, create_pkce_challenge, create_pkce_verifier, create_state, validate_state
from src.providers.base import ProviderError

RAW_EMAIL = b"From: Sender <sender@example.com>\r\nTo: user@example.com\r\nSubject: Hello\r\nMessage-ID: <m1@example.com>\r\n\r\nHello team."


def test_oauth_state_and_pkce_helpers():
    state, verifier = create_state(), create_pkce_verifier()
    challenge = create_pkce_challenge(verifier)
    assert len(state) >= 16 and len(challenge) >= 32
    assert validate_state(state, state)
    assert not validate_state(state, "attacker-state")
    url = build_authorization_url(OAuthConfig("https://example.com/authorize", "client", "https://app.example/callback", ("mail.read",)), state)
    assert "client_id=client" in url and "state=" in url


def test_gmail_read_only_adapter_parses_raw_mime():
    raw_b64 = base64.urlsafe_b64encode(RAW_EMAIL).decode().rstrip("=")
    def handler(request):
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "m1"}]})
        return httpx.Response(200, json={"raw": raw_b64})
    adapter = GmailAdapter("token", transport=httpx.MockTransport(handler))
    try:
        assert adapter.list_message_ids(limit=1)[0].message_id == "m1"
        assert adapter.fetch_message("m1").sender.address == "sender@example.com"
    finally:
        adapter.close()


def test_gmail_provider_failure_is_wrapped():
    adapter = GmailAdapter("token", transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    with pytest.raises(ProviderError):
        adapter.list_message_ids()
    adapter.close()


def test_outlook_adapter_normalizes_graph_message():
    def handler(request):
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"value": [{"id": "m1"}]})
        return httpx.Response(200, json={"id": "m1","subject":"Hello","from":{"emailAddress":{"address":"sender@example.com","name":"Sender"}},"toRecipients":[{"emailAddress":{"address":"user@example.com"}}],"ccRecipients":[],"body":{"contentType":"text","content":"Hello"},"internetMessageHeaders":[{"name":"Authentication-Results","value":"spf=pass"}],"receivedDateTime":"2026-10-07T00:00:00Z"})
    adapter = OutlookAdapter("token", transport=httpx.MockTransport(handler))
    try:
        assert adapter.list_message_ids(limit=1)[0].message_id == "m1"
        assert adapter.fetch_message("m1").recipients == ("user@example.com",)
    finally:
        adapter.close()
