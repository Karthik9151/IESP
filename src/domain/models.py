from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SecurityClassification(str, Enum):
    PHISHING = "PHISHING"
    SUSPICIOUS = "SUSPICIOUS"
    NON_PHISHING = "NON-PHISHING"
    REVIEW_REQUIRED = "REVIEW REQUIRED"


class PriorityLabel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Sender:
    address: str
    display_name: str = ""
    domain: str = ""


@dataclass(frozen=True)
class HeaderData:
    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AttachmentMetadata:
    filename: str
    content_type: str
    size_bytes: int | None = None
    disposition: str | None = None


@dataclass(frozen=True)
class UrlMetadata:
    url: str
    scheme: str | None = None
    hostname: str | None = None
    port: int | None = None
    userinfo_present: bool = False


@dataclass(frozen=True)
class EmailMessage:
    message_id: str
    sender: Sender
    recipients: tuple[str, ...]
    subject: str = ""
    text_body: str = ""
    html_body: str = ""
    headers: HeaderData = field(default_factory=HeaderData)
    attachments: tuple[AttachmentMetadata, ...] = ()
    urls: tuple[UrlMetadata, ...] = ()
    received_at: datetime | None = None


@dataclass(frozen=True)
class SecuritySignal:
    code: str
    severity: Severity
    category: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityAnalysis:
    signals: tuple[SecuritySignal, ...] = ()
    parser_ok: bool = True


@dataclass(frozen=True)
class SecurityDecision:
    classification: SecurityClassification
    reasons: tuple[SecuritySignal, ...] = ()
    phishing_score: float | None = None
    phishing_label: int | None = None


@dataclass(frozen=True)
class PriorityResult:
    label: PriorityLabel
    proxy_label: bool = True
    score_by_class: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    message_id: str
    security: SecurityDecision
    priority: PriorityResult | None = None
    request_id: str | None = None
