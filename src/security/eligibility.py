from src.domain.models import SecurityClassification


def is_priority_eligible(classification: SecurityClassification) -> bool:
    return classification is SecurityClassification.NON_PHISHING
