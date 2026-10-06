from __future__ import annotations

import logging
import re
import time
import uuid
from pathlib import Path

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.models import (
    AnalysisResult,
    AttachmentMetadata,
    EmailMessage,
    HeaderData,
    Sender,
)
from src.security.engine import SecurityEngine
from .auth import AuthorizationContext, authorize_analysis, require_api_key
from .schemas import (
    AnalysisResponse, EmailRequest, HealthResponse, PriorityResponse,
    ReadyResponse, SecurityReason, SecurityResponse,
)
from .service import AnalysisService, build_analysis_service
from .settings import Settings

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _to_email(payload: EmailRequest) -> EmailMessage:
    from email.utils import parseaddr
    address = parseaddr(payload.sender)[1]
    if "@" not in address:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "Invalid sender address."})
    sender_domain = address.rsplit("@", 1)[1].lower().rstrip(".")
    urls = []
    from src.parsing.email_parser import _extract_urls
    urls = _extract_urls(payload.text_body + "\n" + payload.html_body)
    if len(urls) > 50:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "Too many URLs in message content."})
    attachments = tuple(
        AttachmentMetadata(a.filename, a.content_type, a.size_bytes, a.disposition)
        for a in payload.attachments
    )
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
    reasons = [
        SecurityReason(code=r.code, severity=r.severity.value, category=r.category, message=r.message, evidence=r.evidence)
        for r in result.security.reasons
    ]
    priority = None
    if result.priority is not None:
        priority = PriorityResponse(
            label=result.priority.label.value,
            proxy_label=result.priority.proxy_label,
            score_by_class=result.priority.score_by_class,
        )
    return AnalysisResponse(
        message_id=result.message_id,
        request_id=result.request_id or "",
        security=SecurityResponse(classification=result.security.classification.value, reasons=reasons),
        priority=priority,
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
        if not request_id or not _REQUEST_ID_RE.fullmatch(request_id):
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                too_large = int(content_length) > settings.max_request_bytes
            except ValueError:
                return JSONResponse(status_code=400, content={"code": "INVALID_CONTENT_LENGTH", "message": "Invalid request."})
            if too_large:
                return JSONResponse(status_code=413, content={"code": "REQUEST_TOO_LARGE", "message": "Request exceeds configured size limit.", "request_id": request_id})
        return await call_next(request)

    @app.exception_handler(Exception)
    async def safe_exception_handler(request: Request, exc: Exception):
        logging.getLogger("iesp").exception("request_failed request_id=%s error_type=%s", getattr(request.state, "request_id", ""), type(exc).__name__)
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
    async def analyze(
        payload: EmailRequest,
        context: AuthorizationContext = Depends(require_api_key(settings)),
    ):
        authorize_analysis(context)
        started = time.perf_counter()
        result = service.analyze(_to_email(payload), request.state.request_id)
        logging.getLogger("iesp").info(
            "analysis_completed request_id=%s decision=%s duration_ms=%.2f",
            request.state.request_id,
            result.security.classification.value,
            (time.perf_counter() - started) * 1000,
        )
        return _response(result)

    return app


app = create_app()
