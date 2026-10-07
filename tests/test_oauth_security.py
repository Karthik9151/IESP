import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.oauth_store import OAuthStore
from backend.app.settings import Settings

def test_oauth_state_is_bound_and_single_use(tmp_path):
    s=Settings(environment="test",database_path=Path(tmp_path)/"db.sqlite3",database_url="",allowed_origins=("http://localhost:5173",))
    store=OAuthStore(s)
    store.create_state("state-1234567890123456",1,2,"session-a","gmail","verifier")
    assert store.consume_state("state-1234567890123456","session-b","gmail") is None
    got=store.consume_state("state-1234567890123456","session-a","gmail")
    assert got and got["user_id"]==1 and got["workspace_id"]==2
    assert store.consume_state("state-1234567890123456","session-a","gmail") is None

def test_oauth_tokens_are_not_stored_plaintext(tmp_path):
    s=Settings(environment="test",database_path=Path(tmp_path)/"db.sqlite3",database_url="",allowed_origins=("http://localhost:5173",))
    store=OAuthStore(s)
    store.upsert_connection(user_id=1,workspace_id=2,provider="gmail",account_id="a",account_email="a@example.com",access_token="access-secret",refresh_token="refresh-secret",expires_at=datetime.now(timezone.utc),scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    db=Path(tmp_path)/"db.sqlite3"
    raw=db.read_bytes()
    assert b"access-secret" not in raw and b"refresh-secret" not in raw
    rows=store.get_connections(2,"gmail")
    assert rows[0]["access_token"]=="access-secret"
    assert rows[0]["refresh_token"]=="refresh-secret"
