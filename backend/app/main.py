from __future__ import annotations
import logging,re,time,uuid
from email.utils import parseaddr
from fastapi import Depends,FastAPI,HTTPException,Request,UploadFile,File
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,Response
from src.domain.models import AttachmentMetadata,EmailMessage,HeaderData,Sender
from src.parsing.email_parser import EmailParseError,_extract_urls,parse_email_bytes,parse_email_text
from .auth import AuthorizationContext,clear_session,hash_password,issue_session,require_session,verify_password
from .rate_limit import RateLimiter
from .schemas import *
from .service import AnalysisService,build_analysis_service
from .settings import Settings
LOGGER=logging.getLogger('iesp'); RID=re.compile(r'^[A-Za-z0-9._:-]{1,128}$')
def _email(p:EmailRequest):
    a=parseaddr(p.sender)[1]
    if '@' not in a: raise HTTPException(422,detail={'code':'INVALID_SENDER','message':'Invalid sender address.'})
    urls=_extract_urls(p.text_body+'\n'+p.html_body)
    if len(urls)>50: raise HTTPException(422,detail={'code':'TOO_MANY_URLS','message':'Too many URLs in message content.'})
    return EmailMessage(p.message_id,Sender(a,a.split('@',1)[0],a.rsplit('@',1)[1].lower().rstrip('.')),tuple(p.recipients),p.subject,p.text_body,p.html_body,HeaderData({k.lower():v for k,v in p.headers.items()}),tuple(AttachmentMetadata(x.filename,x.content_type,x.size_bytes,x.disposition) for x in p.attachments),urls,p.received_timestamp)
def _risk(c): return {'PHISHING':90,'SUSPICIOUS':65,'REVIEW REQUIRED':45,'NON-PHISHING':10}.get(c,50)
def _out(r):
    reasons=[SecurityReason(code=x.code,severity=x.severity.value,category=x.category,message=x.message,evidence=x.evidence) for x in r.security.reasons]
    score=r.security.phishing_score
    priority=PriorityResponse(label=r.priority.label.value,proxy_label=r.priority.proxy_label,score_by_class=r.priority.score_by_class) if r.priority else None
    return AnalysisResponse(message_id=r.message_id,request_id=r.request_id or '',security=SecurityResponse(classification=r.security.classification.value,risk_score=_risk(r.security.classification.value),model_score=score,model_score_kind='decision_margin' if score is not None else 'unavailable',reasons=reasons),priority=priority,model_info=ModelInfoResponse(phishing='TF-IDF + LinearSVC' if score is not None else 'unavailable',priority='configured priority model' if priority else None,model_version='IESP-configured-model',policy_version='policy-v1'))
def create_app(settings:Settings|None=None,service:AnalysisService|None=None):
    settings=settings or Settings(); settings.validate(); service=service or build_analysis_service(settings); limiter=RateLimiter(); app=FastAPI(title='IESP API',version='1.1.0',docs_url=None if settings.environment=='production' else '/docs')
    app.add_middleware(CORSMiddleware,allow_origins=list(settings.allowed_origins),allow_credentials=True,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Request-ID'])
    @app.middleware('http')
    async def guard(request,call_next):
        rid=request.headers.get('X-Request-ID') if request.headers.get('X-Request-ID') and RID.fullmatch(request.headers['X-Request-ID']) else str(uuid.uuid4()); request.state.request_id=rid
        cl=request.headers.get('content-length')
        if cl and cl.isdigit() and int(cl)>settings.max_request_bytes:return JSONResponse(413,content={'code':'REQUEST_TOO_LARGE','message':'Request exceeds configured size limit.','request_id':rid})
        response=await call_next(request); response.headers['X-Request-ID']=rid; response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else response.headers.get('Cache-Control',''); return response
    @app.exception_handler(RequestValidationError)
    async def validation(request,exc): return JSONResponse(422,content={'code':'VALIDATION_ERROR','message':'Request validation failed.','request_id':request.state.request_id})
    @app.exception_handler(Exception)
    async def errors(request,exc):
        LOGGER.error('request_failed request_id=%s error_type=%s',request.state.request_id,type(exc).__name__)
        return JSONResponse(500,content={'code':'INTERNAL_ERROR','message':'IESP could not complete this request.','request_id':request.state.request_id})
    session=Depends(require_session(service.repository,settings))
    @app.get('/health',response_model=HealthResponse)
    async def health():return HealthResponse(status='ok')
    @app.get('/ready',response_model=ReadyResponse)
    async def ready():
        blockers=[] 
        if getattr(service.engine,'phishing_model',None) is None:blockers.append('phishing_model_unavailable')
        if not service.repository.ping():blockers.append('database_unavailable')
        return JSONResponse(503 if blockers else 200,content=ReadyResponse(status='not_ready' if blockers else 'ready',blockers=blockers).model_dump())
    @app.post('/api/v1/auth/register',response_model=SessionResponse)
    async def register(p:RegisterRequest):
        try:u=service.repository.register_user(p.email,hash_password(p.password))
        except ValueError as e:
            if str(e)=='EMAIL_EXISTS':raise HTTPException(409,detail={'code':'EMAIL_EXISTS','message':'An account already exists for that email.'})
            raise
        token=issue_session(service.repository,u['id'],u['workspace_id'],settings); body=SessionResponse(user=UserResponse(u['id'],u['email']),workspace=WorkspaceResponse(u['workspace_id'],u['workspace_name'],u['role'])); out=JSONResponse(201,content=body.model_dump(mode='json')); out.set_cookie(settings.session_cookie_name,token,max_age=settings.session_ttl_hours*3600,httponly=True,secure=settings.session_cookie_secure,samesite='lax'); return out
    @app.post('/api/v1/auth/login',response_model=SessionResponse)
    async def login(p:LoginRequest):
        u=service.repository.get_user_by_email(p.email)
        if not u or not verify_password(p.password,u['password_hash']):raise HTTPException(401,detail={'code':'AUTH_FAILED','message':'Email or password is incorrect.'})
        token=issue_session(service.repository,u['id'],u['workspace_id'],settings); body=SessionResponse(user=UserResponse(u['id'],u['email']),workspace=WorkspaceResponse(u['workspace_id'],u['workspace_name'],u['role'])); out=JSONResponse(content=body.model_dump(mode='json')); out.set_cookie(settings.session_cookie_name,token,max_age=settings.session_ttl_hours*3600,httponly=True,secure=settings.session_cookie_secure,samesite='lax'); return out
    @app.post('/api/v1/auth/logout',status_code=204)
    async def logout(request:Request):
        clear_session(service.repository,request.cookies.get(settings.session_cookie_name)); out=Response(status_code=204); out.delete_cookie(settings.session_cookie_name); return out
    @app.get('/api/v1/auth/me',response_model=SessionResponse,dependencies=[session])
    async def me(ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        u=service.repository.get_user_by_email(ctx.email); return SessionResponse(user=UserResponse(u['id'],u['email']),workspace=WorkspaceResponse(u['workspace_id'],u['workspace_name'],u['role']))
    @app.post('/api/v1/analyze',response_model=AnalysisResponse,dependencies=[session])
    async def analyze(request:Request,p:EmailRequest,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        limiter.check(f'analysis:{ctx.user_id}',settings.analysis_rate_limit,settings.analysis_rate_window_seconds); return _out(service.analyze(_email(p),request.state.request_id,ctx.user_id,ctx.workspace_id))
    @app.post('/api/v1/analyze/raw',response_model=AnalysisResponse,dependencies=[session])
    async def raw(request:Request,p:dict,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        raw=p.get('raw_email','')
        if not isinstance(raw,str) or not raw:raise HTTPException(422,detail={'code':'INVALID_RAW_EMAIL','message':'raw_email is required.'})
        if len(raw)>settings.max_email_bytes:raise HTTPException(413,detail={'code':'EMAIL_TOO_LARGE','message':'The email is too large.'})
        try:e=parse_email_text(raw,max_chars=settings.max_email_bytes)
        except EmailParseError as ex:raise HTTPException(422,detail={'code':'EMAIL_PARSE_ERROR','message':str(ex)})
        limiter.check(f'analysis:{ctx.user_id}',settings.analysis_rate_limit,settings.analysis_rate_window_seconds); return _out(service.analyze(e,request.state.request_id,ctx.user_id,ctx.workspace_id))
    @app.post('/api/v1/analyze/eml',response_model=AnalysisResponse,dependencies=[session])
    async def eml(request:Request,file:UploadFile=File(...),ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        if not (file.filename or '').lower().endswith('.eml'):raise HTTPException(422,detail={'code':'UNSUPPORTED_FILE','message':'Only .eml files are accepted.'})
        raw=await file.read(settings.max_email_bytes+1); await file.close()
        if len(raw)>settings.max_email_bytes:raise HTTPException(413,detail={'code':'EMAIL_TOO_LARGE','message':'The email is too large.'})
        try:e=parse_email_bytes(raw,max_bytes=settings.max_email_bytes)
        except EmailParseError as ex:raise HTTPException(422,detail={'code':'EMAIL_PARSE_ERROR','message':str(ex)})
        limiter.check(f'analysis:{ctx.user_id}',settings.analysis_rate_limit,settings.analysis_rate_window_seconds); return _out(service.analyze(e,request.state.request_id,ctx.user_id,ctx.workspace_id))
    @app.get('/api/v1/stats',response_model=StatsResponse,dependencies=[session])
    async def stats(ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):return StatsResponse(**service.stats(ctx.workspace_id))
    @app.get('/api/v1/recent',response_model=PaginatedAnalysisResponse,dependencies=[session])
    async def recent(ctx:AuthorizationContext=Depends(require_session(service.repository,settings)),limit:int=20):
        items=service.recent(ctx.workspace_id,limit); return PaginatedAnalysisResponse(items=[RecentAnalysisItem(**x) for x in items],total=len(items))
    @app.get('/api/v1/analysis/{message_id}',dependencies=[session])
    async def analysis(message_id:str,ctx:AuthorizationContext=Depends(require_session(service.repository,settings))):
        x=service.get(ctx.workspace_id,message_id)
        if not x:raise HTTPException(404,detail={'code':'NOT_FOUND','message':'Analysis not found.'})
        return x
    return app
app=create_app()
