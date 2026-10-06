from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+._^|~-]+$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AttachmentRequest(StrictModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=256)
    size_bytes: int | None = Field(default=None, ge=0, le=10 * 1024 * 1024)
    disposition: Literal["inline", "attachment"] | None = None


class EmailRequest(StrictModel):
    message_id: str = Field(min_length=1, max_length=512)
    sender: str = Field(min_length=3, max_length=1024)
    recipients: list[str] = Field(min_length=1, max_length=50)
    subject: str = Field(default="", max_length=1000)
    text_body: str = Field(default="", max_length=500_000)
    html_body: str = Field(default="", max_length=500_000)
    headers: dict[str, str] = Field(default_factory=dict, max_length=100)
    attachments: list[AttachmentRequest] = Field(default_factory=list, max_length=25)
    received_timestamp: datetime | None = None

    @field_validator("message_id", "sender", "subject", "text_body", "html_body", mode="before")
    @classmethod
    def safe_text(cls, value):
        if not isinstance(value, str):
            raise ValueError("String value required")
        if any(ch in value for ch in ("\x00", "\r")):
            raise ValueError("NUL and carriage-return characters are not allowed")
        return value

    @field_validator("recipients")
    @classmethod
    def safe_recipients(cls, values):
        for value in values:
            if not isinstance(value, str) or any(ch in value for ch in ("\r", "\n", "\x00")):
                raise ValueError("Invalid recipient value")
        return values

    @field_validator("headers")
    @classmethod
    def safe_headers(cls, values):
        for name, value in values.items():
            if not _HEADER_NAME_RE.fullmatch(name):
                raise ValueError("Invalid header name")
            if not isinstance(value, str) or any(ch in value for ch in ("\r", "\n", "\x00")):
                raise ValueError("Invalid header value")
            if len(value) > 8192:
                raise ValueError("Header value too long")
        return values


class SecurityReason(StrictModel):
    code: str
    severity: str
    category: str
    message: str
    evidence: dict = Field(default_factory=dict)


class SecurityResponse(StrictModel):
    classification: Literal["PHISHING", "SUSPICIOUS", "NON-PHISHING", "REVIEW REQUIRED"]
    reasons: list[SecurityReason] = Field(default_factory=list)


class PriorityResponse(StrictModel):
    label: Literal["P1", "P2", "P3"]
    proxy_label: bool = True
    score_by_class: dict[str, float] = Field(default_factory=dict)


class AnalysisResponse(StrictModel):
    message_id: str
    request_id: str
    security: SecurityResponse
    priority: PriorityResponse | None = None


class HealthResponse(StrictModel):
    status: Literal["ok"]


class ReadyResponse(StrictModel):
    status: Literal["ready", "not_ready"]
    blockers: list[str] = Field(default_factory=list)
