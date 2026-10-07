from __future__ import annotations

from pathlib import Path

import yaml

from src.security.engine import SecurityEngine, SklearnPhishingPredictor, SklearnPriorityPredictor

from .repository import build_repository


class AnalysisService:
    def __init__(self, engine, repository, model_version: str = "models-v1", policy_version: str = "policy-v1"):
        self.engine = engine
        self.repository = repository
        self.model_version = model_version
        self.policy_version = policy_version

    def analyze(self, email, request_id, user_id, workspace_id):
        result = self.engine.analyze(email, request_id=request_id)
        self.repository.save(
            result,
            email,
            user_id,
            workspace_id,
            self.model_version,
            self.policy_version,
        )
        return result

    def stats(self, workspace_id, high_risk_threshold=75.0):
        return self.repository.stats(workspace_id, high_risk_threshold)

    def history(self, workspace_id, **filters):
        return self.repository.history(workspace_id, **filters)

    def recent(self, workspace_id, limit=20):
        return self.repository.history(workspace_id, page=1, page_size=limit)["items"]

    def get(self, workspace_id, message_id):
        return self.repository.get(workspace_id, message_id)


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build_analysis_service(settings):
    security_config = _load_yaml(settings.security_config).get("security", {})
    phishing = priority = None

    if settings.phishing_artifact.exists():
        try:
            from src.ml.phishing.predict import load_phishing_model

            phishing = SklearnPhishingPredictor(load_phishing_model(settings.phishing_artifact))
        except Exception:
            phishing = None

    if settings.priority_artifact.exists():
        try:
            from src.ml.priority.predict import load_priority_model

            priority = SklearnPriorityPredictor(load_priority_model(settings.priority_artifact))
        except Exception:
            priority = None

    return AnalysisService(
        SecurityEngine(security_config, phishing, priority),
        build_repository(settings),
        settings.model_version,
        settings.policy_version,
    )
