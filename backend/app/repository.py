from __future__ import annotations
from typing import Protocol
from src.domain.models import AnalysisResult

class AnalysisRepository(Protocol):
    def save(self, result: AnalysisResult) -> None: ...

class NoOpAnalysisRepository:
    """M5 persistence boundary; intentionally does not persist email content."""
    def save(self, result: AnalysisResult) -> None:
        return None
