from __future__ import annotations

from src.domain.models import SecurityAnalysis, SecurityClassification, SecurityDecision, SecuritySignal, Severity

_RANK = {Severity.INFO: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}


def decide_security(analysis: SecurityAnalysis, *, phishing_label: int | None, phishing_score: float | None, config: dict | None = None) -> SecurityDecision:
    cfg = config or {}
    pcfg = cfg.get("phishing", {})
    scfg = cfg.get("suspicious", {})
    if not analysis.parser_ok or any(_RANK[s.severity] >= _RANK[Severity.CRITICAL] for s in analysis.signals):
        return SecurityDecision(SecurityClassification.REVIEW_REQUIRED, analysis.signals, phishing_score, phishing_label)

    strong = float(pcfg.get("strong_score_threshold", 1.0))
    positive = float(pcfg.get("suspicious_score_threshold", 0.0))
    high_count = sum(_RANK[s.severity] >= _RANK[Severity.HIGH] for s in analysis.signals)
    meaningful_count = sum(_RANK[s.severity] >= _RANK[Severity.MEDIUM] for s in analysis.signals)
    ml_strong = phishing_score is not None and phishing_score >= strong
    ml_positive = phishing_label == 1 or (phishing_score is not None and phishing_score >= positive)
    reasons = list(analysis.signals)

    if ml_strong and high_count >= int(pcfg.get("supporting_high_signals", 1)):
        reasons.append(SecuritySignal("PHISHING_ML", Severity.HIGH, "PHISHING_ML", "Strong phishing ranking score with supporting security indicators.", {"score": phishing_score}))
        return SecurityDecision(SecurityClassification.PHISHING, tuple(reasons), phishing_score, phishing_label)
    if ml_positive and phishing_score is not None:
        reasons.append(SecuritySignal("PHISHING_ML", Severity.MEDIUM, "PHISHING_ML", "Phishing model produced positive evidence without enough supporting evidence for a phishing decision.", {"score": phishing_score, "label": phishing_label}))
        return SecurityDecision(SecurityClassification.SUSPICIOUS, tuple(reasons), phishing_score, phishing_label)
    if meaningful_count >= int(scfg.get("minimum_meaningful_signals", 1)):
        return SecurityDecision(SecurityClassification.SUSPICIOUS, tuple(reasons), phishing_score, phishing_label)
    if phishing_score is None and cfg.get("require_phishing_model", True):
        reasons.append(SecuritySignal("POLICY_CONFLICT", Severity.MEDIUM, "POLICY_CONFLICT", "Phishing evidence is unavailable, so the engine fails closed to review.", {}))
        return SecurityDecision(SecurityClassification.REVIEW_REQUIRED, tuple(reasons), None, phishing_label)
    return SecurityDecision(SecurityClassification.NON_PHISHING, tuple(reasons), phishing_score, phishing_label)
