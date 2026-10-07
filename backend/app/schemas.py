from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.models import SecurityClassification


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(StrictModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Valid email required")
        return value


class LoginRequest(RegisterRequest):
    pass


class UserResponse(StrictModel):
    id: int
    email: str


class WorkspaceResponse(StrictModel):
    id: int
    name: str
    role: str


class SessionResponse(StrictModel):
    user: UserResponse
    workspace: WorkspaceResponse


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

    @field_validator("message_id", "sender", "subject", mode="before")
    @classmethod
    def single_line(cls, value: object) -> object:
        if not isinstance(value, str) or any(char in value for char in ("\x00", "\r", "\n")):
            raise ValueError("Invalid text value")
        return value

    @field_validator("text_body", "html_body", mode="before")
    @classmethod
    def body_safe(cls, value: object) -> object:
        if not isinstance(value, str) or "\x00" in value or "\r" in value:
            raise ValueError("Invalid body value")
        return value

    @field_validator("recipients", mode="before")
    @classmethod
    def recipients_safe(cls, value: object) -> object:
        if not isinstance(value, list) or not value:
            raise ValueError("At least one recipient is required")
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip() or any(char in item for char in ("\x00", "\r", "\n")):
                raise ValueError("Invalid recipient")
            cleaned.append(item.strip())
        return cleaned

    @field_validator("headers")
    @classmethod
    def headers_safe(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not re.fullmatch(r"[A-Za-z0-9!#$%&'*+._^|~-]+", key):
                raise ValueError("Invalid header")
            if not isinstance(item, str) or any(char in item for char in ("\x00", "\r", "\n")):
                raise ValueError("Invalid header")
            if len(item) > 8192:
                raise ValueError("Invalid header")
        return value


class RawEmailRequest(StrictModel):
    raw_email: str = Field(min_length=1, max_length=2_000_000)


class SecurityReason(StrictModel):
    code: str
    severity: str
    category: str
    message: str
    evidence: dict = Field(default_factory=dict)


class SecurityResponse(StrictModel):
    classification: str
    risk_score: float = Field(ge=0, le=100)
    model_score: float | None = None
    model_score_kind: Literal["decision_margin", "unavailable"]
    reasons: list[SecurityReason]


class PriorityResponse(StrictModel):
    label: str
    proxy_label: bool = True
    score_by_class: dict[str, float] = Field(default_factory=dict)


class ModelInfoResponse(StrictModel):
    phishing: str
    priority: str | None = None
    model_version: str
    policy_version: str


class EmailMetadataResponse(StrictModel):
    message_id: str
    sender: str
    recipients: list[str]
    subject: str


class AnalysisResponse(StrictModel):
    message_id: str
    request_id: str
    analyzed_at: datetime
    email: EmailMetadataResponse
    security: SecurityResponse
    priority: PriorityResponse | None = None
    model_info: ModelInfoResponse


class RecentAnalysisItem(StrictModel):
    message_id: str
    request_id: str
    sender: str
    recipients: list[str]
    subject: str
    classification: str
    risk_score: float
    priority: str | None
    created_at: datetime


class PaginatedAnalysisResponse(StrictModel):
    items: list[RecentAnalysisItem]
    total: int
    page: int = 1
    page_size: int = 25
    pages: int = 0


class StatsResponse(StrictModel):
    total: int
    phishing: int
    suspicious: int
    non_phishing: int
    review_required: int
    high_risk: int
    high_risk_percentage: float


class ReportSummaryResponse(StrictModel):
    generated_at: datetime
    stats: StatsResponse
    threat_distribution: dict[str, int]
    high_risk_items: list[RecentAnalysisItem]


class ReportExportResponse(StrictModel):
    generated_at: datetime
    items: list[RecentAnalysisItem]


class HealthResponse(StrictModel):
    status: Literal["ok"]


class ReadyResponse(StrictModel):
    status: Literal["ready", "not_ready"]
    blockers: list[str] = Field(default_factory=list)


class ErrorBody(StrictModel):
    code: str
    message: str
    request_id: str
    retry_after_seconds: int | None = None


class ErrorResponse(StrictModel):
    error: ErrorBody


SUPPORTED_CLASSIFICATIONS = {item.value for item in SecurityClassification}
