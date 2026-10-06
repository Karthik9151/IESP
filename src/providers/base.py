from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.models import EmailMessage


class ProviderError(RuntimeError):
    """Provider failure that must not bypass the IESP security pipeline."""


@dataclass(frozen=True)
class ProviderMessageRef:
    provider: str
    message_id: str


class MailProvider(Protocol):
    name: str
    READ_SCOPE: str

    def list_message_ids(self, *, limit: int = 20) -> list[ProviderMessageRef]: ...
    def fetch_message(self, message_id: str) -> EmailMessage: ...
    def analyze_message(self, message_id: str, engine, *, request_id: str | None = None): ...
