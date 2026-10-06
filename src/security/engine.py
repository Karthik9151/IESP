from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.models import AnalysisResult, EmailMessage, PriorityResult

from .analysis import analyze_email_security
from .decision import decide_security
from .eligibility import is_priority_eligible


class PhishingPredictor(Protocol):
    def predict(self, text: str) -> tuple[int, float]: ...


class PriorityPredictor(Protocol):
    def predict(self, text: str) -> PriorityResult: ...


@dataclass
class SecurityEngine:
    config: dict
    phishing_model: PhishingPredictor | None = None
    priority_model: PriorityPredictor | None = None

    def analyze(self, email: EmailMessage, *, request_id: str | None = None) -> AnalysisResult:
        security_analysis = analyze_email_security(email, self.config, parser_ok=True)
        phishing_label = phishing_score = None
        if self.phishing_model is not None:
            phishing_label, phishing_score = self.phishing_model.predict(f"{email.subject}\n{email.text_body}".strip())
        decision = decide_security(security_analysis, phishing_label=phishing_label, phishing_score=phishing_score, config=self.config)
        priority = None
        if is_priority_eligible(decision.classification) and self.priority_model is not None:
            priority = self.priority_model.predict(f"{email.subject}\n{email.text_body}".strip())
        return AnalysisResult(email.message_id, decision, priority, request_id)


class SklearnPhishingPredictor:
    def __init__(self, model): self.model = model

    def predict(self, text: str) -> tuple[int, float]:
        from src.ml.phishing.predict import predict_labels, predict_scores
        return int(predict_labels(self.model, [text])[0]), float(predict_scores(self.model, [text])[0])


class SklearnPriorityPredictor:
    def __init__(self, model): self.model = model

    def predict(self, text: str) -> PriorityResult:
        from src.ml.priority.predict import predict_priority
        return predict_priority(self.model, text)
