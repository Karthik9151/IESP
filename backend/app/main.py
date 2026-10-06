from __future__ import annotations

import logging
import re
import time
import uuid
from email.utils import parseaddr

import yaml
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.models import (
    AnalysisResult,
    AttachmentMetadata,
    EmailMessage,
    HeaderData,
    Sender,
)
from src.parsing.email_parser import _extract_urls
from src.security.engine import SecurityEngine
from .auth import AuthorizationContext, authorize_analysis, require_api_key
from .schemas import (
    AnalysisResponse,
    EmailRequest,
    HealthResponse,
    ModelInfoResponse,
    PriorityResponse,
    ReadyResponse,
    SecurityReason,
    SecurityResponse,
    StatsResponse,
)
from .service import AnalysisService, build_analysis_service
from .settings import Settings

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
LOGGER = logging.getLogger("iesp")


def _to_email(payload: EmailRequest) -> EmailMessage:
    address = parseaddr(payload.sender)[1]
    if "@" not in address:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "Invalid sender address."})
    sender_domain = address.rsplit("@", 1)[1].lower().rstrip(".")
    urls = _extract_urls(f"{payload.text_body}\n{payload.html_body}")
    if len(urls) > 50:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "Too many URLs in message content."})
    attachments = tuple(AttachmentMetadata(a.filename, a.content_type, a.size_bytes, a.disposition) for a in payload.attachments)
    return EmailMessage(
        message_id=payload.message_id,
        sender=Sender(address, address.split("@", 1)[0], sender_domain),
        recipients=tuple(payload.recipients),
        subject=payload.subject,
        text_body=payload.text_body,
        html_body=payload.html_body,
        headers=HeaderData({k.lower(): v for k, v in payload.headers.items()}),
        attachments=attachments,
        urls=urls,
        received_at=payload.received_timestamp,
    )


def _response(result: AnalysisResult) -> AnalysisResponse:
    reasons = [SecurityReason(code=r.code, severity=r.severity.value, category=r.category, message=r.message, evidence=r.evidence) for r in result.security.reasons]
    priority = None
    if result.priority is not None:
        priority = PriorityResponse(label=result.priority.label.value, proxy_label=result.priority.proxy_label, score_by_class=result.priority.score_by_class)
    return AnalysisResponse(
        message_id=result.message_id,
        request_id=result.request_id or "",
        security=SecurityResponse(classification=result.security.classification.value, reasons=reasons),
        priority=priority,
        model_info=ModelInfoResponse(
            phishing="TF-IDF + LinearSVC" if result.security.phishing_score is not None else "unavailable",
            priority="VADER + engineered features + Logistic Regression" if priority else None,
        ),
    )


def create_app(settings: Settings | None = None, service: AnalysisService | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.validate()
    service = service or build_analysis_service(settings)
    app = FastAPI(title="IESP API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_guard(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id or not REQUEST_ID_RE.fullmatch(request_id):
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"code": "INVALID_CONTENT_LENGTH", "message": "Invalid request."})
            if size > settings.max_request_bytes:
                return JSONResponse(status_code=413, content={"code": "REQUEST_TOO_LARGE", "message": "Request exceeds configured size limit.", "request_id": request_id})
        return await call_next(request)

    @app.exception_handler(Exception)
    async def safe_exception_handler(request: Request, exc: Exception):
        LOGGER.error("request_failed request_id=%s error_type=%s", getattr(request.state, "request_id", ""), type(exc).__name__)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "message": "Internal server error.", "request_id": getattr(request.state, "request_id", "")})

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok")

    @app.get("/ready", response_model=ReadyResponse)
    async def ready():
        blockers = []
        if service.engine.phishing_model is None:
            blockers.append("phishing_model_unavailable")
        if service.engine.priority_model is None:
            blockers.append("priority_model_unavailable")
        if blockers:
            return JSONResponse(status_code=503, content=ReadyResponse(status="not_ready", blockers=blockers).model_dump())
        return ReadyResponse(status="ready", blockers=[])

    @app.post("/api/v1/analyze", response_model=AnalysisResponse)
    async def analyze(request: Request, payload: EmailRequest, context: AuthorizationContext = Depends(require_api_key(settings))):
        authorize_analysis(context)
        started = time.perf_counter()
        result = service.analyze(_to_email(payload), request.state.request_id)
        LOGGER.info("analysis_completed request_id=%s message_id=%s decision=%s duration_ms=%.2f", request.state.request_id, result.message_id, result.security.classification.value, (time.perf_counter() - started) * 1000)
        return _response(result)

    @app.get("/api/v1/stats", response_model=StatsResponse)
    async def stats(context: AuthorizationContext = Depends(require_api_key(settings))):
        authorize_analysis(context)
        return StatsResponse(**service.stats())

    @app.get("/api/v1/recent")
    async def recent(limit: int = 20, context: AuthorizationContext = Depends(require_api_key(settings))):
        authorize_analysis(context)
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=422, detail={"code": "INVALID_LIMIT", "message": "Limit must be 1-100."})
        return {"items": service.recent(limit)}

    @app.get("/api/v1/analysis/{message_id}")
    async def analysis(message_id: str, context: AuthorizationContext = Depends(require_api_key(settings))):
        authorize_analysis(context)
        result = service.get(message_id)
        if result is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Analysis not found."})
        return result

    return app


app = create_app()
