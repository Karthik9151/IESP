from __future__ import annotations

import base64
import hashlib
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

class OAuthStore:
    def __init__(self, settings):
        self.settings = settings
        raw_key = os.getenv("IESP_OAUTH_ENCRYPTION_KEY", "")
        if not raw_key:
            if settings.environment == "production":
                raise ValueError("IESP_OAUTH_ENCRYPTION_KEY is required in production")
            raw_key = base64.urlsafe_b64encode(hashlib.sha256(b"iesp-development-oauth-key").digest()).decode()
        self.fernet = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        self.is_pg = settings.database_url.startswith(("postgres://", "postgresql://"))
        self._init_schema()

    def _connect(self):
        if self.is_pg:
            import psycopg
            return psycopg.connect(self.settings.database_url)
        conn = sqlite3.connect(self.settings.database_path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        if self.is_pg:
            schema = """
            CREATE TABLE IF NOT EXISTS oauth_states(
              state_hash TEXT PRIMARY KEY,user_id BIGINT NOT NULL,workspace_id BIGINT NOT NULL,
              session_hash TEXT NOT NULL,provider TEXT NOT NULL,code_verifier_enc TEXT NOT NULL,
              expires_at TIMESTAMPTZ NOT NULL,consumed_at TIMESTAMPTZ
            );
            CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry ON oauth_states(expires_at);
            CREATE TABLE IF NOT EXISTS provider_connections(
              id BIGSERIAL PRIMARY KEY,user_id BIGINT NOT NULL,workspace_id BIGINT NOT NULL,
              provider TEXT NOT NULL,provider_account_id TEXT NOT NULL,provider_account_email TEXT,
              access_token_enc TEXT,refresh_token_enc TEXT,access_expires_at TIMESTAMPTZ,
              scopes TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
              UNIQUE(workspace_id,provider,provider_account_id)
            );
            CREATE INDEX IF NOT EXISTS idx_provider_connections_owner ON provider_connections(workspace_id,provider);
            """
            with self._connect() as c:
                c.execute(schema)
                c.commit()
        else:
            schema = """
            CREATE TABLE IF NOT EXISTS oauth_states(
              state_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,
              session_hash TEXT NOT NULL,provider TEXT NOT NULL,code_verifier_enc TEXT NOT NULL,
              expires_at TEXT NOT NULL,consumed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry ON oauth_states(expires_at);
            CREATE TABLE IF NOT EXISTS provider_connections(
              id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,
              provider TEXT NOT NULL,provider_account_id TEXT NOT NULL,provider_account_email TEXT,
              access_token_enc TEXT,refresh_token_enc TEXT,access_expires_at TEXT,
              scopes TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
              UNIQUE(workspace_id,provider,provider_account_id)
            );
            CREATE INDEX IF NOT EXISTS idx_provider_connections_owner ON provider_connections(workspace_id,provider);
            """
            with self._connect() as c:
                c.executescript(schema)
                c.commit()

    @staticmethod
    def hash_state(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def hash_session(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def create_state(self, state: str, user_id: int, workspace_id: int, session_token: str, provider: str, verifier: str) -> None:
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=10)
        values=(self.hash_state(state),user_id,workspace_id,self.hash_session(session_token),provider,self.fernet.encrypt(verifier.encode()).decode(),expiry)
        if self.is_pg:
            sql="""INSERT INTO oauth_states(state_hash,user_id,workspace_id,session_hash,provider,code_verifier_enc,expires_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s)"""
        else:
            values=(*values,expiry.isoformat())
            sql="""INSERT INTO oauth_states(state_hash,user_id,workspace_id,session_hash,provider,code_verifier_enc,expires_at)
                   VALUES(?,?,?,?,?,?,?)"""
        with self._connect() as c:
            c.execute(sql, values)
            c.commit()

    def consume_state(self, state: str, session_token: str, provider: str) -> dict[str,Any] | None:
        state_hash=self.hash_state(state); session_hash=self.hash_session(session_token)
        now=datetime.now(timezone.utc)
        with self._connect() as c:
            if self.is_pg:
                row=c.execute("""SELECT * FROM oauth_states WHERE state_hash=%s AND consumed_at IS NULL
                                 AND provider=%s AND session_hash=%s AND expires_at>%s FOR UPDATE""",
                              (state_hash,provider,session_hash,now)).fetchone()
                if not row: return None
                c.execute("UPDATE oauth_states SET consumed_at=%s WHERE state_hash=%s",(now,state_hash))
                c.commit()
                return {"user_id":int(row[1]),"workspace_id":int(row[2]),"verifier":self.fernet.decrypt(row[5].encode()).decode()}
            row=c.execute("""SELECT * FROM oauth_states WHERE state_hash=? AND consumed_at IS NULL
                             AND provider=? AND session_hash=?""",(state_hash,provider,session_hash)).fetchone()
            if not row: return None
            expiry=datetime.fromisoformat(row[6])
            if expiry<=now: return None
            c.execute("UPDATE oauth_states SET consumed_at=? WHERE state_hash=?",(now.isoformat(),state_hash))
            c.commit()
            return {"user_id":int(row[1]),"workspace_id":int(row[2]),"verifier":self.fernet.decrypt(row[5].encode()).decode()}

    def upsert_connection(self, *, user_id:int, workspace_id:int, provider:str, account_id:str, account_email:str|None,
                          access_token:str|None, refresh_token:str|None, expires_at:datetime|None, scopes:list[str]) -> None:
        now=datetime.now(timezone.utc)
        access_enc=self.fernet.encrypt(access_token.encode()).decode() if access_token else None
        refresh_enc=self.fernet.encrypt(refresh_token.encode()).decode() if refresh_token else None
        scope_text=" ".join(sorted(set(scopes)))
        if self.is_pg:
            sql="""INSERT INTO provider_connections
              (user_id,workspace_id,provider,provider_account_id,provider_account_email,access_token_enc,refresh_token_enc,access_expires_at,scopes,created_at,updated_at)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(workspace_id,provider,provider_account_id) DO UPDATE SET
              user_id=EXCLUDED.user_id,provider_account_email=EXCLUDED.provider_account_email,
              access_token_enc=COALESCE(EXCLUDED.access_token_enc,provider_connections.access_token_enc),
              refresh_token_enc=COALESCE(EXCLUDED.refresh_token_enc,provider_connections.refresh_token_enc),
              access_expires_at=EXCLUDED.access_expires_at,scopes=EXCLUDED.scopes,updated_at=EXCLUDED.updated_at"""
            values=(user_id,workspace_id,provider,account_id,account_email,access_enc,refresh_enc,expires_at,scope_text,now,now)
        else:
            sql="""INSERT INTO provider_connections
              (user_id,workspace_id,provider,provider_account_id,provider_account_email,access_token_enc,refresh_token_enc,access_expires_at,scopes,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(workspace_id,provider,provider_account_id) DO UPDATE SET
              user_id=excluded.user_id,provider_account_email=excluded.provider_account_email,
              access_token_enc=COALESCE(excluded.access_token_enc,provider_connections.access_token_enc),
              refresh_token_enc=COALESCE(excluded.refresh_token_enc,provider_connections.refresh_token_enc),
              access_expires_at=excluded.access_expires_at,scopes=excluded.scopes,updated_at=excluded.updated_at"""
            values=(user_id,workspace_id,provider,account_id,account_email,access_enc,refresh_enc,expires_at.isoformat() if expires_at else None,scope_text,now.isoformat(),now.isoformat())
        with self._connect() as c:
            c.execute(sql,values); c.commit()

    def get_connections(self, workspace_id:int, provider:str|None=None) -> list[dict[str,Any]]:
        if self.is_pg:
            sql="SELECT id,provider,provider_account_id,provider_account_email,access_token_enc,refresh_token_enc,access_expires_at,scopes FROM provider_connections WHERE workspace_id=%s"
            args=[workspace_id]
        else:
            sql="SELECT id,provider,provider_account_id,provider_account_email,access_token_enc,refresh_token_enc,access_expires_at,scopes FROM provider_connections WHERE workspace_id=?"
            args=[workspace_id]
        if provider:
            sql+=" AND provider="+("%s" if self.is_pg else "?"); args.append(provider)
        with self._connect() as c: rows=c.execute(sql,args).fetchall()
        result=[]
        for row in rows:
            d=dict(row) if not self.is_pg else {"id":row[0],"provider":row[1],"provider_account_id":row[2],"provider_account_email":row[3],"access_token_enc":row[4],"refresh_token_enc":row[5],"access_expires_at":row[6],"scopes":row[7]}
            d["access_token"]=self.fernet.decrypt(d.pop("access_token_enc").encode()).decode() if d.get("access_token_enc") else None
            d["refresh_token"]=self.fernet.decrypt(d.pop("refresh_token_enc").encode()).decode() if d.get("refresh_token_enc") else None
            d["scopes"]=d["scopes"].split() if d["scopes"] else []
            result.append(d)
        return result

    def delete_connection(self, workspace_id:int, provider:str) -> None:
        sql="DELETE FROM provider_connections WHERE workspace_id="+("%s" if self.is_pg else "?")+" AND provider="+("%s" if self.is_pg else "?")
        with self._connect() as c: c.execute(sql,(workspace_id,provider)); c.commit()
