from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .auth import AuthorizationContext, require_session, token_hash
from .oauth_store import OAuthStore

GMAIL_SCOPE="https://www.googleapis.com/auth/gmail.readonly"
MICROSOFT_SCOPE="Mail.Read"
STANDARD_MS_SCOPES=("openid","profile","offline_access")

def _config(settings, provider):
    if provider=="gmail":
        return {
            "client_id":__import__("os").getenv("GOOGLE_CLIENT_ID",""),
            "client_secret":__import__("os").getenv("GOOGLE_CLIENT_SECRET",""),
            "redirect_uri":__import__("os").getenv("GOOGLE_REDIRECT_URI",""),
            "authorize":"https://accounts.google.com/o/oauth2/v2/auth",
            "token":"https://oauth2.googleapis.com/token",
        }
    return {
        "client_id":__import__("os").getenv("MICROSOFT_CLIENT_ID",""),
        "client_secret":__import__("os").getenv("MICROSOFT_CLIENT_SECRET",""),
        "redirect_uri":__import__("os").getenv("MICROSOFT_REDIRECT_URI",""),
        "tenant":__import__("os").getenv("MICROSOFT_TENANT_ID","common"),
        "authorize":f"https://login.microsoftonline.com/{__import__('os').getenv('MICROSOFT_TENANT_ID','common')}/oauth2/v2.0/authorize",
        "token":f"https://login.microsoftonline.com/{__import__('os').getenv('MICROSOFT_TENANT_ID','common')}/oauth2/v2.0/token",
    }

def _configured(cfg):
    return all(cfg.get(k) for k in ("client_id","client_secret","redirect_uri"))

def _pkce():
    verifier=secrets.token_urlsafe(48)
    digest=hashlib.sha256(verifier.encode()).digest()
    challenge=base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier,challenge

def create_oauth_router(settings, service):
    router=APIRouter(prefix="/api/v1/oauth", tags=["oauth"])
    store=OAuthStore(settings)
    frontend=__import__("os").getenv("IESP_FRONTEND_URL", settings.allowed_origins[0] if settings.allowed_origins else "/")

    @router.get("/{provider}/start")
    async def oauth_start(provider:str, request:Request, ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        cfg=_config(settings,provider)
        if not _configured(cfg): raise HTTPException(503,detail={"code":"OAUTH_NOT_CONFIGURED","message":"Provider OAuth is not configured."})
        raw_session=request.cookies.get(settings.session_cookie_name)
        if not raw_session: raise HTTPException(401,detail={"code":"AUTH_REQUIRED","message":"Authentication is required."})
        state=secrets.token_urlsafe(32); verifier,challenge=_pkce()
        store.create_state(state,ctx.user_id,ctx.workspace_id,raw_session,provider,verifier)
        scopes=[GMAIL_SCOPE] if provider=="gmail" else [*STANDARD_MS_SCOPES,MICROSOFT_SCOPE]
        params={"client_id":cfg["client_id"],"redirect_uri":cfg["redirect_uri"],"response_type":"code","scope":" ".join(scopes),"state":state,"code_challenge":challenge,"code_challenge_method":"S256"}
        if provider=="gmail": params.update({"access_type":"offline","include_granted_scopes":"true","prompt":"consent"})
        return RedirectResponse(cfg["authorize"]+"?"+urlencode(params),status_code=302)

    @router.get("/{provider}/callback")
    async def oauth_callback(provider:str, request:Request, code:str|None=None, state:str|None=None, error:str|None=None):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        raw_session=request.cookies.get(settings.session_cookie_name)
        if not raw_session or not state: return RedirectResponse(frontend+"?oauth="+provider+"&status=failed",303)
        state_data=store.consume_state(state,raw_session,provider)
        if not state_data: return RedirectResponse(frontend+"?oauth="+provider+"&status=invalid_state",303)
        if error or not code: return RedirectResponse(frontend+"?oauth="+provider+"&status=denied",303)
        cfg=_config(settings,provider)
        data={"client_id":cfg["client_id"],"client_secret":cfg["client_secret"],"code":code,"redirect_uri":cfg["redirect_uri"],"grant_type":"authorization_code","code_verifier":state_data["verifier"]}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                token_response=await client.post(cfg["token"],data=data)
                if token_response.status_code>=400: return RedirectResponse(frontend+"?oauth="+provider+"&status=token_error",303)
                tokens=token_response.json()
        except httpx.HTTPError:
            return RedirectResponse(frontend+"?oauth="+provider+"&status=provider_unavailable",303)
        access=tokens.get("access_token"); refresh=tokens.get("refresh_token")
        if not access: return RedirectResponse(frontend+"?oauth="+provider+"&status=token_missing",303)
        scopes=(tokens.get("scope") or "").split()
        if provider=="gmail":
            if GMAIL_SCOPE not in scopes: return RedirectResponse(frontend+"?oauth=gmail&status=scope_denied",303)
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    profile=(await client.get("https://gmail.googleapis.com/gmail/v1/users/me/profile",headers={"Authorization":"Bearer "+access})).json()
                account_id=profile.get("emailAddress")
                account_email=account_id
            except Exception:
                return RedirectResponse(frontend+"?oauth=gmail&status=profile_error",303)
        else:
            if MICROSOFT_SCOPE not in scopes: return RedirectResponse(frontend+"?oauth=microsoft&status=scope_denied",303)
            id_token=tokens.get("id_token","")
            try:
                unverified=jwt.decode(id_token,options={"verify_signature":False,"verify_aud":False})
                account_id=unverified.get("sub")
                account_email=unverified.get("preferred_username") or unverified.get("email")
                if not account_id: raise ValueError("missing subject")
            except Exception:
                return RedirectResponse(frontend+"?oauth=microsoft&status=identity_error",303)
        expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(tokens.get("expires_in",3600)))
        store.upsert_connection(user_id=state_data["user_id"],workspace_id=state_data["workspace_id"],provider=provider,account_id=account_id,account_email=account_email,access_token=access_token,refresh_token=refresh,expires_at=expires_at,scopes=scopes)
        return RedirectResponse(frontend+"?oauth="+provider+"&status=connected",303)

    @router.get("/connections")
    async def connections(ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        rows=store.get_connections(ctx.workspace_id)
        return [{"provider":r["provider"],"account_id":r["provider_account_id"],"account_email":r["provider_account_email"],"scopes":r["scopes"],"expires_at":r["access_expires_at"]} for r in rows]

    @router.delete("/{provider}")
    async def disconnect(provider:str,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if provider not in ("gmail","microsoft"): raise HTTPException(404,detail={"code":"PROVIDER_NOT_FOUND","message":"Provider is not supported."})
        store.delete_connection(ctx.workspace_id,provider)
        return JSONResponse({"status":"disconnected"})

    async def access_token(ctx,provider):
        rows=store.get_connections(ctx.workspace_id,provider)
        if not rows: raise HTTPException(404,detail={"code":"PROVIDER_NOT_CONNECTED","message":"Provider is not connected."})
        row=rows[0]; expires=row["access_expires_at"]
        if isinstance(expires,str): expires=datetime.fromisoformat(expires.replace("Z","+00:00"))
        if expires and expires>datetime.now(timezone.utc)+timedelta(minutes=2): return row["access_token"]
        refresh=row["refresh_token"]
        if not refresh: raise HTTPException(401,detail={"code":"PROVIDER_REAUTH_REQUIRED","message":"Provider authorization must be renewed."})
        cfg=_config(settings,provider)
        scope=" ".join([GMAIL_SCOPE] if provider=="gmail" else [*STANDARD_MS_SCOPES,MICROSOFT_SCOPE])
        data={"client_id":cfg["client_id"],"client_secret":cfg["client_secret"],"refresh_token":refresh,"grant_type":"refresh_token","scope":scope}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response=await client.post(cfg["token"],data=data)
                if response.status_code>=400: raise ValueError("refresh_failed")
                tokens=response.json()
        except Exception:
            store.delete_connection(ctx.workspace_id,provider)
            raise HTTPException(401,detail={"code":"PROVIDER_REAUTH_REQUIRED","message":"Provider authorization is no longer valid."})
        access=tokens.get("access_token")
        if not access: raise HTTPException(401,detail={"code":"PROVIDER_REAUTH_REQUIRED","message":"Provider authorization is no longer valid."})
        new_refresh=tokens.get("refresh_token")
        expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(tokens.get("expires_in",3600)))
        store.upsert_connection(user_id=ctx.user_id,workspace_id=ctx.workspace_id,provider=provider,account_id=row["provider_account_id"],account_email=row["provider_account_email"],access_token=access,refresh_token=new_refresh,expires_at=expires_at,scopes=tokens.get("scope","").split() or row["scopes"])
        return access

    @router.get("/{provider}/messages")
    async def list_messages(provider:str,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        token=await access_token(ctx,provider)
        from src.providers.gmail import GmailAdapter
        from src.providers.outlook import OutlookAdapter
        adapter=GmailAdapter(token) if provider=="gmail" else OutlookAdapter(token)
        try: return [{"provider":x.provider,"message_id":x.message_id} for x in adapter.list_message_ids(limit=20)]
        finally: adapter.close()

    @router.post("/{provider}/messages/{message_id}/analyze",response_model=None)
    async def analyze_provider_message(provider:str,message_id:str,request:Request,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        token=await access_token(ctx,provider)
        from src.providers.gmail import GmailAdapter
        from src.providers.outlook import OutlookAdapter
        adapter=GmailAdapter(token) if provider=="gmail" else OutlookAdapter(token)
        try: result=adapter.analyze_message(message_id,service,request_id=request.state.request_id)
        except Exception:
            raise HTTPException(502,detail={"code":"PROVIDER_MESSAGE_ERROR","message":"The provider message could not be retrieved or analyzed safely."})
        finally: adapter.close()
        email=adapter.fetch_message(message_id) if False else None
        row=service.get(ctx.workspace_id,result.message_id)
        if row: return row
        return {"message_id":result.message_id,"request_id":result.request_id,"classification":result.security.classification.value,"risk_score":result.security.phishing_score}
    return router
