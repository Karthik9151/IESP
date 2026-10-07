from __future__ import annotations

import csv
import io
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from email.utils import parseaddr

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from src.domain.models import AttachmentMetadata, EmailMessage, HeaderData, Sender
from src.parsing.email_parser import EmailParseError, _extract_urls, parse_email_bytes, parse_email_text
from src.security.logging_policy import log_decision

from .auth import AuthorizationContext, clear_session, hash_password, issue_session, require_session, verify_password
from .rate_limit import RateLimiter
from .risk import policy_risk_score
from .schemas import (
    AnalysisResponse, EmailMetadataResponse, EmailRequest, ErrorResponse, HealthResponse, LoginRequest,
    ModelInfoResponse, PaginatedAnalysisResponse, PriorityResponse, RawEmailRequest, ReadyResponse,
    RegisterRequest, ReportExportResponse, ReportSummaryResponse, SecurityReason, SecurityResponse, SessionResponse, StatsResponse,
    UserResponse, WorkspaceResponse, SUPPORTED_CLASSIFICATIONS,
)
from .service import AnalysisService, build_analysis_service
from .settings import Settings

LOGGER = logging.getLogger("iesp")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

def _error_schema(description: str) -> dict:
    return {"model": ErrorResponse, "description": description}


AUTH_ERROR = _error_schema("Authentication is required or the session is invalid.")
VALIDATION_ERROR = _error_schema("Request validation or parsing failed.")
INTERNAL_ERROR = _error_schema("The server could not complete the request.")
RATE_LIMIT_ERROR = _error_schema("The authenticated user exceeded the analysis rate limit.")


def _error_response(request: Request, code: str, message: str, status_code: int, *, headers=None, retry_after_seconds=None):
    body = {"error": {"code": code, "message": message, "request_id": request.state.request_id, "retry_after_seconds": retry_after_seconds}}
    return JSONResponse(status_code=status_code, content=ErrorResponse.model_validate(body).model_dump(mode="json"), headers=headers or {})


def _email_from_request(payload: EmailRequest) -> EmailMessage:
    sender = parseaddr(payload.sender)[1].strip()
    if "@" not in sender or "\r" in sender or "\n" in sender:
        raise HTTPException(422, detail={"code": "INVALID_SENDER", "message": "Invalid sender address."})
    recipients = []
    for address in payload.recipients:
        parsed = parseaddr(address)[1].strip()
        if "@" not in parsed or "\r" in parsed or "\n" in parsed:
            raise HTTPException(422, detail={"code": "INVALID_RECIPIENT", "message": "Invalid recipient address."})
        recipients.append(parsed)
    urls = _extract_urls(f"{payload.text_body}\n{payload.html_body}")
    if len(urls) > 50:
        raise HTTPException(422, detail={"code": "TOO_MANY_URLS", "message": "Too many URLs in message content."})
    return EmailMessage(
        message_id=payload.message_id,
        sender=Sender(
            address=sender,
            display_name=parseaddr(payload.sender)[0][:256],
            domain=sender.rsplit("@", 1)[1].lower().rstrip("."),
        ),
        recipients=tuple(recipients),
        subject=payload.subject,
        text_body=payload.text_body,
        html_body=payload.html_body,
        headers=HeaderData({key.lower(): value for key, value in payload.headers.items()}),
        attachments=tuple(AttachmentMetadata(item.filename, item.content_type, item.size_bytes, item.disposition) for item in payload.attachments),
        urls=urls,
        received_at=payload.received_timestamp,
    )


def _ensure_aware_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _analysis_response(email, result, settings: Settings, analyzed_at: datetime) -> AnalysisResponse:
    reasons = [SecurityReason(code=item.code, severity=item.severity.value, category=item.category, message=item.message, evidence=item.evidence) for item in result.security.reasons]
    serialized = [item.model_dump() for item in reasons]
    score = result.security.phishing_score
    priority = PriorityResponse(label=result.priority.label.value, proxy_label=result.priority.proxy_label, score_by_class=result.priority.score_by_class) if result.priority else None
    return AnalysisResponse(
        message_id=result.message_id,
        request_id=result.request_id or "",
        analyzed_at=analyzed_at,
        email=EmailMetadataResponse(message_id=email.message_id, sender=email.sender.address, recipients=list(email.recipients), subject=email.subject),
        security=SecurityResponse(
            classification=result.security.classification.value,
            risk_score=policy_risk_score(result.security.classification.value, serialized),
            model_score=score,
            model_score_kind="decision_margin" if score is not None else "unavailable",
            reasons=reasons,
        ),
        priority=priority,
        model_info=ModelInfoResponse(
            phishing="TF-IDF + LinearSVC decision margin" if score is not None else "unavailable",
            priority="VADER + engineered features + Logistic Regression" if priority else None,
            model_version=settings.model_version,
            policy_version=settings.policy_version,
        ),
    )


def _stored_analysis_response(row, settings: Settings) -> AnalysisResponse:
    return AnalysisResponse(
        message_id=row["message_id"],
        request_id=row["request_id"],
        analyzed_at=_ensure_aware_datetime(row["created_at"]),
        email=EmailMetadataResponse(message_id=row["message_id"], sender=row["sender"], recipients=row.get("recipients", []), subject=row.get("subject", "")),
        security=SecurityResponse(
            classification=row["classification"],
            risk_score=float(row["risk_score"]),
            model_score=float(row["model_score"]) if row.get("model_score") is not None else None,
            model_score_kind="decision_margin" if row.get("model_score") is not None else "unavailable",
            reasons=[SecurityReason(**reason) for reason in row.get("reasons", [])],
        ),
        priority=PriorityResponse(label=row["priority"], proxy_label=True, score_by_class={}) if row.get("priority") else None,
        model_info=ModelInfoResponse(
            phishing="TF-IDF + LinearSVC decision margin" if row.get("model_score") is not None else "unavailable",
            priority="configured priority model" if row.get("priority") else None,
            model_version=row["model_version"],
            policy_version=row["policy_version"],
        ),
    )


def _history_item(row):
    from .schemas import RecentAnalysisItem
    return RecentAnalysisItem(
        message_id=row["message_id"],
        request_id=row["request_id"],
        sender=row["sender"],
        recipients=row.get("recipients", []),
        subject=row.get("subject", ""),
        classification=row["classification"],
        risk_score=float(row["risk_score"]),
        priority=row.get("priority"),
        created_at=_ensure_aware_datetime(row["created_at"]),
    )


def _log_analysis(result, request: Request, started: float):
    log_decision(
        LOGGER,
        request_id=request.state.request_id,
        message_id=result.message_id,
        decision=result.security.classification.value,
        reason_codes=[item.code for item in result.security.reasons],
        duration_ms=(time.perf_counter() - started) * 1000,
    )


def create_app(settings: Settings | None = None, service: AnalysisService | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.validate()
    service = service or build_analysis_service(settings)
    limiter = RateLimiter()
    app = FastAPI(
        title="IESP API",
        version="1.2.0",
        docs_url=None if settings.environment == "production" else "/docs",
        redoc_url=None if settings.environment == "production" else "/redoc",
    )
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Request-ID"])

    @app.middleware("http")
    async def guard(request: Request, call_next):
        raw_request_id = request.headers.get("X-Request-ID")
        request.state.request_id = raw_request_id if raw_request_id and REQUEST_ID_RE.fullmatch(raw_request_id) else str(uuid.uuid4())
        body = await request.body()
        if len(body) > settings.max_request_bytes:
            return _error_response(request, "REQUEST_TOO_LARGE", "Request exceeds configured size limit.", 413)
        try:
            response = await call_next(request)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            return _error_response(request, detail.get("code", "HTTP_ERROR"), detail.get("message", "Request failed."), exc.status_code, headers=dict(exc.headers or {}), retry_after_seconds=detail.get("retry_after_seconds"))
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.environment == "production":
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return _error_response(request, "VALIDATION_ERROR", "Request validation failed.", 422)

    @app.exception_handler(HTTPException)
    async def http_exception(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        return _error_response(request, detail.get("code", "HTTP_ERROR"), detail.get("message", "Request failed."), exc.status_code, headers=dict(exc.headers or {}), retry_after_seconds=detail.get("retry_after_seconds"))

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        LOGGER.error("request_failed request_id=%s error_type=%s", request.state.request_id, type(exc).__name__)
        return _error_response(request, "INTERNAL_ERROR", "IESP could not complete this request.", 500)

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok")

    @app.get("/ready", response_model=ReadyResponse, responses={503: {"model": ReadyResponse, "description": "Required model or database dependency is unavailable."}})
    async def ready():
        blockers = []
        if getattr(service.engine, "phishing_model", None) is None:
            blockers.append("phishing_model_unavailable")
        if not service.repository.ping():
            blockers.append("database_unavailable")
        return JSONResponse(status_code=503 if blockers else 200, content=ReadyResponse(status="not_ready" if blockers else "ready", blockers=blockers).model_dump(mode="json"))

    @app.post("/api/v1/auth/register", response_model=SessionResponse, status_code=201, responses={409: _error_schema("Email is already registered."), 422: VALIDATION_ERROR, 500: INTERNAL_ERROR})
    async def register(payload: RegisterRequest):
        try:
            user = service.repository.register_user(payload.email, hash_password(payload.password))
        except ValueError as exc:
            if str(exc) == "EMAIL_EXISTS":
                raise HTTPException(409, detail={"code": "EMAIL_EXISTS", "message": "An account already exists for that email."}) from exc
            raise
        token = issue_session(service.repository, user["id"], user["workspace_id"], settings)
        body = SessionResponse(
            user=UserResponse(id=user["id"], email=user["email"]),
            workspace=WorkspaceResponse(id=user["workspace_id"], name=user["workspace_name"], role=user["role"]),
        )
        response = JSONResponse(status_code=201, content=body.model_dump(mode="json"))
        response.set_cookie(settings.session_cookie_name, token, max_age=settings.session_ttl_hours * 3600, httponly=True, secure=settings.session_cookie_secure, samesite=settings.session_cookie_samesite)
        return response

    @app.post("/api/v1/auth/login", response_model=SessionResponse, responses={401: AUTH_ERROR, 422: VALIDATION_ERROR, 500: INTERNAL_ERROR})
    async def login(payload: LoginRequest):
        user = service.repository.get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(401, detail={"code": "AUTH_FAILED", "message": "Email or password is incorrect."})
        token = issue_session(service.repository, user["id"], user["workspace_id"], settings)
        body = SessionResponse(
            user=UserResponse(id=user["id"], email=user["email"]),
            workspace=WorkspaceResponse(id=user["workspace_id"], name=user["workspace_name"], role=user["role"]),
        )
        response = JSONResponse(content=body.model_dump(mode="json"))
        response.set_cookie(settings.session_cookie_name, token, max_age=settings.session_ttl_hours * 3600, httponly=True, secure=settings.session_cookie_secure, samesite=settings.session_cookie_samesite)
        return response

    @app.post("/api/v1/auth/logout", status_code=204, responses={500: INTERNAL_ERROR})
    async def logout(request: Request):
        clear_session(service.repository, request.cookies.get(settings.session_cookie_name))
        response = Response(status_code=204)
        response.delete_cookie(settings.session_cookie_name)
        return response

    @app.get("/api/v1/auth/me", response_model=SessionResponse, responses={401: AUTH_ERROR, 500: INTERNAL_ERROR})
    async def me(ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        user = service.repository.get_user(ctx.user_id, ctx.workspace_id)
        if not user:
            raise HTTPException(401, detail={"code": "SESSION_INVALID", "message": "Authentication is required."})
        return SessionResponse(
            user=UserResponse(id=user["id"], email=user["email"]),
            workspace=WorkspaceResponse(id=user["workspace_id"], name=user["workspace_name"], role=user["role"]),
        )

    def rate_limit(ctx: AuthorizationContext):
        limiter.check(f"analysis:{ctx.user_id}", settings.analysis_rate_limit, settings.analysis_rate_window_seconds)

    @app.post("/api/v1/analyze", response_model=AnalysisResponse, responses={401: AUTH_ERROR, 413: VALIDATION_ERROR, 422: VALIDATION_ERROR, 429: RATE_LIMIT_ERROR, 500: INTERNAL_ERROR})
    async def analyze(request: Request, payload: EmailRequest, ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        rate_limit(ctx)
        email = _email_from_request(payload)
        started = time.perf_counter()
        result = service.analyze(email, request.state.request_id, ctx.user_id, ctx.workspace_id)
        _log_analysis(result, request, started)
        return _analysis_response(email, result, settings, analyzed_at=datetime.now(timezone.utc))

    @app.post("/api/v1/analyze/raw", response_model=AnalysisResponse, responses={401: AUTH_ERROR, 413: VALIDATION_ERROR, 422: VALIDATION_ERROR, 429: RATE_LIMIT_ERROR, 500: INTERNAL_ERROR})
    async def analyze_raw(request: Request, payload: RawEmailRequest, ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        if len(payload.raw_email.encode("utf-8")) > settings.max_email_bytes:
            raise HTTPException(413, detail={"code": "EMAIL_TOO_LARGE", "message": "The email is too large."})
        try:
            email = parse_email_text(payload.raw_email, max_chars=settings.max_email_bytes)
        except EmailParseError as exc:
            raise HTTPException(422, detail={"code": "EMAIL_PARSE_ERROR", "message": str(exc)}) from exc
        rate_limit(ctx)
        started = time.perf_counter()
        result = service.analyze(email, request.state.request_id, ctx.user_id, ctx.workspace_id)
        _log_analysis(result, request, started)
        return _analysis_response(email, result, settings, analyzed_at=datetime.now(timezone.utc))

    @app.post("/api/v1/analyze/eml", response_model=AnalysisResponse, responses={401: AUTH_ERROR, 413: VALIDATION_ERROR, 422: VALIDATION_ERROR, 429: RATE_LIMIT_ERROR, 500: INTERNAL_ERROR})
    async def analyze_eml(request: Request, file: UploadFile = File(...), ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        filename = file.filename or ""
        if not filename.lower().endswith(".eml"):
            raise HTTPException(422, detail={"code": "UNSUPPORTED_FILE", "message": "Only .eml files are accepted."})
        raw = await file.read(settings.max_email_bytes + 1)
        await file.close()
        if len(raw) > settings.max_email_bytes:
            raise HTTPException(413, detail={"code": "EMAIL_TOO_LARGE", "message": "The email is too large."})
        try:
            email = parse_email_bytes(raw, max_bytes=settings.max_email_bytes)
        except EmailParseError as exc:
            raise HTTPException(422, detail={"code": "EMAIL_PARSE_ERROR", "message": str(exc)}) from exc
        rate_limit(ctx)
        started = time.perf_counter()
        result = service.analyze(email, request.state.request_id, ctx.user_id, ctx.workspace_id)
        _log_analysis(result, request, started)
        return _analysis_response(email, result, settings, analyzed_at=datetime.now(timezone.utc))

    @app.get("/api/v1/stats", response_model=StatsResponse, responses={401: AUTH_ERROR, 500: INTERNAL_ERROR})
    async def stats(ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        return StatsResponse(**service.stats(ctx.workspace_id, settings.high_risk_threshold))

    @app.get("/api/v1/recent", response_model=PaginatedAnalysisResponse, responses={401: AUTH_ERROR, 422: VALIDATION_ERROR, 500: INTERNAL_ERROR})
    async def recent(ctx: AuthorizationContext = Depends(require_session(service.repository, settings)), limit: int = Query(20, ge=1, le=100)):
        rows = service.recent(ctx.workspace_id, limit)
        return PaginatedAnalysisResponse(items=[_history_item(row) for row in rows], total=len(rows), page=1, page_size=limit, pages=1 if rows else 0)

    @app.get("/api/v1/history", response_model=PaginatedAnalysisResponse, responses={401: AUTH_ERROR, 422: VALIDATION_ERROR, 500: INTERNAL_ERROR})
    async def history(
        ctx: AuthorizationContext = Depends(require_session(service.repository, settings)),
        page: int = Query(1, ge=1),
        page_size: int = Query(settings.history_page_size, ge=1, le=100),
        q: str | None = Query(None, max_length=200),
        classification: str | None = Query(None),
        min_risk: float | None = Query(None, ge=0, le=100),
        max_risk: float | None = Query(None, ge=0, le=100),
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = Query("created_at", pattern=r"^(created_at|risk_score|classification|sender|subject)$"),
        sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    ):
        if min_risk is not None and max_risk is not None and min_risk > max_risk:
            raise HTTPException(422, detail={"code": "INVALID_RISK_RANGE", "message": "min_risk cannot exceed max_risk."})
        if classification and classification not in SUPPORTED_CLASSIFICATIONS:
            raise HTTPException(422, detail={"code": "INVALID_CLASSIFICATION", "message": "Unsupported classification filter."})
        data = service.history(ctx.workspace_id, page=page, page_size=page_size, search=q, classification=classification, min_risk=min_risk, max_risk=max_risk, date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order)
        return PaginatedAnalysisResponse(items=[_history_item(row) for row in data["items"]], total=data["total"], page=data["page"], page_size=data["page_size"], pages=data["pages"])

    @app.get("/api/v1/analysis/{message_id}", response_model=AnalysisResponse, responses={401: AUTH_ERROR, 404: _error_schema("Analysis was not found in the current workspace."), 500: INTERNAL_ERROR})
    async def analysis(message_id: str, ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        row = service.get(ctx.workspace_id, message_id)
        if not row:
            raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Analysis not found."})
        return _stored_analysis_response(row, settings)

    @app.get("/api/v1/reports/summary", response_model=ReportSummaryResponse, responses={401: AUTH_ERROR, 500: INTERNAL_ERROR})
    async def report_summary(ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        stats = service.stats(ctx.workspace_id, settings.high_risk_threshold)
        high_risk = service.history(ctx.workspace_id, page=1, page_size=10, min_risk=settings.high_risk_threshold, sort_by="risk_score", sort_order="desc")["items"]
        return ReportSummaryResponse(
            generated_at=datetime.now(timezone.utc),
            stats=StatsResponse(**stats),
            threat_distribution={"PHISHING": stats["phishing"], "SUSPICIOUS": stats["suspicious"], "REVIEW REQUIRED": stats["review_required"], "NON-PHISHING": stats["non_phishing"]},
            high_risk_items=[_history_item(row) for row in high_risk],
        )

    @app.get("/api/v1/reports/export", responses={200: {"description": "Report export in JSON or CSV format.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReportExportResponse"}}, "text/csv": {"schema": {"type": "string"}}}}, 401: AUTH_ERROR, 422: VALIDATION_ERROR, 500: INTERNAL_ERROR})
    async def report_export(format: str = Query("csv", pattern=r"^(csv|json)$"), ctx: AuthorizationContext = Depends(require_session(service.repository, settings))):
        rows = service.history(ctx.workspace_id, page=1, page_size=settings.report_export_limit, sort_by="created_at", sort_order="desc")["items"]
        generated_at = datetime.now(timezone.utc).isoformat()
        if format == "json":
            return JSONResponse(content=ReportExportResponse(generated_at=datetime.fromisoformat(generated_at), items=[_history_item(row) for row in rows]).model_dump(mode="json"))
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["message_id", "request_id", "sender", "recipients", "subject", "classification", "risk_score", "model_score", "priority", "created_at", "model_version", "policy_version"])
        for row in rows:
            writer.writerow([row["message_id"], row["request_id"], row["sender"], "; ".join(row.get("recipients", [])), row.get("subject", ""), row["classification"], row["risk_score"], row["model_score"], row["priority"] or "", row["created_at"], row["model_version"], row["policy_version"]])
        return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="iesp-analysis-report.csv"'})

    return app


app = create_app()
