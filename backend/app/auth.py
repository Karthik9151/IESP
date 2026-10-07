from __future__ import annotations
import hashlib, hmac, secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request

def hash_password(password:str)->str:
    salt=secrets.token_bytes(16); digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1); return 'scrypt$16384$8$1$'+salt.hex()+'$'+digest.hex()
def verify_password(password:str,encoded:str)->bool:
    try:
        prefix,salt_hex,digest_hex=encoded.rsplit('$',2); _,n,r,p=prefix.split('$'); got=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt_hex),n=int(n),r=int(r),p=int(p)); return hmac.compare_digest(got.hex(),digest_hex)
    except (ValueError,TypeError): return False
def token_hash(token:str)->str: return hashlib.sha256(token.encode()).hexdigest()
@dataclass(frozen=True)
class AuthorizationContext:
    user_id:int
    workspace_id:int
    email:str
    role:str
def issue_session(repo,user_id:int,workspace_id:int,settings)->str:
    token=secrets.token_urlsafe(48); repo.create_session(token_hash(token),user_id,workspace_id,datetime.now(timezone.utc)+timedelta(hours=settings.session_ttl_hours)); return token
def clear_session(repo,token):
    if token: repo.delete_session(token_hash(token))
def require_session(repo,settings):
    def dependency(request:Request):
        token=request.cookies.get(settings.session_cookie_name)
        if not token: raise HTTPException(401,detail={'code':'AUTH_REQUIRED','message':'Authentication is required.'})
        row=repo.get_session(token_hash(token))
        if not row: raise HTTPException(401,detail={'code':'SESSION_EXPIRED','message':'Your session has expired.'})
        return AuthorizationContext(int(row['user_id']),int(row['workspace_id']),str(row['email']),str(row['role']))
    return dependency