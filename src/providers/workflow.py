from __future__ import annotations

from src.domain.models import AnalysisResult


def analyze_provider_message(provider, message_id: str, engine, *, request_id: str | None = None) -> AnalysisResult:
    message = provider.fetch_message(message_id)
    return engine.analyze(message, request_id=request_id)
