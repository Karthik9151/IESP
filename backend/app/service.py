from __future__ import annotations
from pathlib import Path
import yaml
from src.domain.models import AnalysisResult, EmailMessage
from src.ml.phishing.predict import load_phishing_model
from src.ml.priority.predict import load_priority_model
from src.security.engine import SecurityEngine, SklearnPhishingPredictor, SklearnPriorityPredictor
from .repository import AnalysisRepository, NoOpAnalysisRepository

class AnalysisService:
    def __init__(self, engine: SecurityEngine, repository: AnalysisRepository | None = None):
        self.engine = engine
        self.repository = repository or NoOpAnalysisRepository()

    def analyze(self, email: EmailMessage, request_id: str) -> AnalysisResult:
        result = self.engine.analyze(email, request_id=request_id)
        self.repository.save(result)
        return result

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def build_analysis_service(settings) -> AnalysisService:
    security_config = _load_yaml(settings.security_config).get("security", {})
    phishing_predictor = priority_predictor = None
    if settings.phishing_artifact.exists():
        try:
            phishing_predictor = SklearnPhishingPredictor(load_phishing_model(settings.phishing_artifact))
        except Exception:
            phishing_predictor = None
    if settings.priority_artifact.exists():
        try:
            priority_predictor = SklearnPriorityPredictor(load_priority_model(settings.priority_artifact))
        except Exception:
            priority_predictor = None
    return AnalysisService(SecurityEngine(security_config, phishing_predictor, priority_predictor))
