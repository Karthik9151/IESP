from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .auth import AuthorizationContext, require_session
from .oauth_store import OAuthStore

GMAIL_SCOPE="https://www.googleapis.com/auth/gmail.readonly"
MICROSOFT_SCOPE="Mail.Read"
STANDARD_MS_SCOPES=("openid","profile","offline_access")

def _config(provider):
    if provider=="gmail":
        return {"client_id":os.getenv("GOOGLE_CLIENT_ID",""),"client_secret":os.getenv("GOOGLE_CLIENT_SECRET",""),
                "redirect_uri":os.getenv("GOOGLE_REDIRECT_URI",""),"authorize":"https://accounts.google.com/o/oauth2/v2/auth",
                "token":"https://oauth2.googleapis.com/token"}
    tenant=os.getenv("MICROSOFT_TENANT_ID","common")
    return {"client_id":os.getenv("MICROSOFT_CLIENT_ID",""),"client_secret":os.getenv("MICROSOFT_CLIENT_SECRET",""),
            "redirect_uri":os.getenv("MICROSOFT_REDIRECT_URI",""),"tenant":tenant,
            "authorize":f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            "token":f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"}

def _pkce():
    verifier=secrets.token_urlsafe(48)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier,challenge

def _configured(cfg):
    return all(cfg.get(k) for k in ("client_id","client_secret","redirect_uri"))

async def _verified_ms_identity(id_token:str,cfg:dict):
    if not id_token: raise ValueError("missing id token")
    async with httpx.AsyncClient(timeout=10) as client:
        discovery=(await client.get(f"https://login.microsoftonline.com/{cfg['tenant']}/v2.0/.well-known/openid-configuration")).json()
    issuer=discovery["issuer"]
    async with httpx.AsyncClient(timeout=10) as client:
        jwks=(await client.get(discovery["jwks_uri"])).json()
    header=jwt.get_unverified_header(id_token)
    key=None
    for candidate in jwks.get("keys",[]):
        if candidate.get("kid")==header.get("kid"):
            key=jwt.algorithms.RSAAlgorithm.from_jwk(candidate)
            break
    if key is None: raise ValueError("unknown signing key")
    claims=jwt.decode(id_token,key=key,algorithms=["RS256"],audience=cfg["client_id"],issuer=issuer)
    subject=claims.get("sub")
    email=claims.get("preferred_username") or claims.get("email")
    if not subject: raise ValueError("missing subject")
    return subject,email

def create_oauth_router(settings, service):
    router=APIRouter(prefix="/api/v1/oauth",tags=["oauth"])
    store=OAuthStore(settings, force_sqlite=service.repository.__class__.__name__.startswith("SQLite"))
    frontend=os.getenv("IESP_FRONTEND_URL",settings.allowed_origins[0] if settings.allowed_origins else "/")

    @router.get("/{provider}/start")
    async def start(provider:str,request:Request,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        cfg=_config(provider)
        if not _configured(cfg): raise HTTPException(503,detail={"code":"OAUTH_NOT_CONFIGURED","message":"Provider OAuth is not configured."})
        session=request.cookies.get(settings.session_cookie_name)
        if not session: raise HTTPException(401,detail={"code":"AUTH_REQUIRED","message":"Authentication is required."})
        state=secrets.token_urlsafe(32); verifier,challenge=_pkce()
        store.create_state(state,ctx.user_id,ctx.workspace_id,session,provider,verifier)
        scopes=[GMAIL_SCOPE] if provider=="gmail" else [*STANDARD_MS_SCOPES,MICROSOFT_SCOPE]
        params={"client_id":cfg["client_id"],"redirect_uri":cfg["redirect_uri"],"response_type":"code","scope":" ".join(scopes),
                "state":state,"code_challenge":challenge,"code_challenge_method":"S256"}
        if provider=="gmail": params.update({"access_type":"offline","include_granted_scopes":"true","prompt":"consent"})
        return RedirectResponse(cfg["authorize"]+"?"+urlencode(params),302)

    @router.get("/{provider}/callback")
    async def callback(provider:str,request:Request,code:str|None=None,state:str|None=None,error:str|None=None):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        session=request.cookies.get(settings.session_cookie_name)
        if not session or not state: return RedirectResponse(f"{frontend}?oauth={provider}&status=failed",303)
        state_data=store.consume_state(state,session,provider)
        if not state_data: return RedirectResponse(f"{frontend}?oauth={provider}&status=invalid_state",303)
        if error or not code: return RedirectResponse(f"{frontend}?oauth={provider}&status=denied",303)
        cfg=_config(provider)
        payload={"client_id":cfg["client_id"],"client_secret":cfg["client_secret"],"code":code,"redirect_uri":cfg["redirect_uri"],
                 "grant_type":"authorization_code","code_verifier":state_data["verifier"]}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response=await client.post(cfg["token"],data=payload)
                if response.status_code>=400: return RedirectResponse(f"{frontend}?oauth={provider}&status=token_error",303)
                tokens=response.json()
        except httpx.HTTPError:
            return RedirectResponse(f"{frontend}?oauth={provider}&status=provider_unavailable",303)
        access=tokens.get("access_token")
        if not access: return RedirectResponse(f"{frontend}?oauth={provider}&status=token_missing",303)
        scopes=(tokens.get("scope") or "").split()
        if provider=="gmail":
            if GMAIL_SCOPE not in scopes: return RedirectResponse(f"{frontend}?oauth=gmail&status=scope_denied",303)
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response=await client.get("https://gmail.googleapis.com/gmail/v1/users/me/profile",headers={"Authorization":f"Bearer {access}"})
                    response.raise_for_status(); profile=response.json()
                account_id=profile["emailAddress"]; account_email=account_id
            except Exception:
                return RedirectResponse(f"{frontend}?oauth=gmail&status=profile_error",303)
        else:
            if MICROSOFT_SCOPE not in scopes: return RedirectResponse(f"{frontend}?oauth=microsoft&status=scope_denied",303)
            try: account_id,account_email=await _verified_ms_identity(tokens.get("id_token",""),cfg)
            except Exception: return RedirectResponse(f"{frontend}?oauth=microsoft&status=identity_error",303)
        expires=datetime.now(timezone.utc)+timedelta(seconds=int(tokens.get("expires_in",3600)))
        store.upsert_connection(user_id=state_data["user_id"],workspace_id=state_data["workspace_id"],provider=provider,
                                account_id=account_id,account_email=account_email,access_token=access,refresh_token=tokens.get("refresh_token"),
                                expires_at=expires,scopes=scopes)
        return RedirectResponse(f"{frontend}?oauth={provider}&status=connected",303)

    @router.get("/connections")
    async def connections(ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        return [{"provider":r["provider"],"account_id":r["provider_account_id"],"account_email":r["provider_account_email"],
                 "scopes":r["scopes"],"expires_at":r["access_expires_at"]} for r in store.get_connections(ctx.workspace_id)]

    @router.delete("/{provider}")
    async def disconnect(provider:str,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        store.delete_connection(ctx.workspace_id,provider); return JSONResponse({"status":"disconnected"})

    async def access_token(ctx,provider):
        rows=store.get_connections(ctx.workspace_id,provider)
        if not rows: raise HTTPException(404,detail={"code":"PROVIDER_NOT_CONNECTED","message":"Provider is not connected."})
        row=rows[0]; expires=row["access_expires_at"]
        if isinstance(expires,str): expires=datetime.fromisoformat(expires.replace("Z","+00:00"))
        if expires and expires>datetime.now(timezone.utc)+timedelta(minutes=2): return row["access_token"]
        if not row["refresh_token"]:
            raise HTTPException(401,detail={"code":"PROVIDER_REAUTH_REQUIRED","message":"Provider authorization must be renewed."})
        cfg=_config(provider)
        scopes=[GMAIL_SCOPE] if provider=="gmail" else [*STANDARD_MS_SCOPES,MICROSOFT_SCOPE]
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response=await client.post(cfg["token"],data={"client_id":cfg["client_id"],"client_secret":cfg["client_secret"],
                    "refresh_token":row["refresh_token"],"grant_type":"refresh_token","scope":" ".join(scopes)})
                if response.status_code>=400: raise ValueError("refresh_failed")
                tokens=response.json()
            access=tokens.get("access_token")
            if not access: raise ValueError("missing_access")
        except Exception:
            store.delete_connection(ctx.workspace_id,provider)
            raise HTTPException(401,detail={"code":"PROVIDER_REAUTH_REQUIRED","message":"Provider authorization is no longer valid."})
        expires=datetime.now(timezone.utc)+timedelta(seconds=int(tokens.get("expires_in",3600)))
        store.upsert_connection(user_id=ctx.user_id,workspace_id=ctx.workspace_id,provider=provider,
                                account_id=row["provider_account_id"],account_email=row["provider_account_email"],access_token=access,
                                refresh_token=tokens.get("refresh_token"),expires_at=expires,scopes=tokens.get("scope","").split() or row["scopes"])
        return access

    @router.get("/{provider}/messages")
    async def messages(provider:str,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        token=await access_token(ctx,provider)
        from src.providers.gmail import GmailAdapter
        from src.providers.outlook import OutlookAdapter
        adapter=GmailAdapter(token) if provider=="gmail" else OutlookAdapter(token)
        try: return [{"provider":x.provider,"message_id":x.message_id} for x in adapter.list_message_ids(limit=20)]
        finally: adapter.close()

    @router.post("/{provider}/messages/{message_id}/analyze")
    async def analyze_message(provider:str,message_id:str,request:Request,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        token=await access_token(ctx,provider)
        from src.providers.gmail import GmailAdapter
        from src.providers.outlook import OutlookAdapter
        adapter=GmailAdapter(token) if provider=="gmail" else OutlookAdapter(token)
        try:
            email=adapter.fetch_message(message_id)
            result=service.analyze(email,request.state.request_id,ctx.user_id,ctx.workspace_id)
            from .main import _analysis_response
            return _analysis_response(email,result,settings,datetime.now(timezone.utc))
        except Exception:
            raise HTTPException(502,detail={"code":"PROVIDER_MESSAGE_ERROR","message":"The provider message could not be retrieved or analyzed safely."})
        finally: adapter.close()

    return router
