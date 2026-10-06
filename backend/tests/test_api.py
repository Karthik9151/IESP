from fastapi.testclient import TestClient
from src.domain.models import (
    AnalysisResult, PriorityLabel, PriorityResult, SecurityClassification,
    SecurityDecision, SecuritySignal, Severity,
)
from src.security.engine import SecurityEngine
from backend.app.main import create_app
from backend.app.service import AnalysisService
from backend.app.settings import Settings


class StubPhishing:
    def __init__(self, label=0, score=-1.0):
        self.label, self.score = label, score
    def predict(self, text):
        return self.label, self.score


class StubPriority:
    def predict(self, text):
        return PriorityResult(PriorityLabel.P2)


def make_client(label=0, score=-1.0, api_key="test-secret"):
    config = {
        "phishing": {"strong_score_threshold": 1.0, "suspicious_score_threshold": 0.0, "supporting_high_signals": 1},
        "suspicious": {"minimum_meaningful_signals": 1},
        "require_phishing_model": True,
        "url": {"max_length": 2048, "max_count": 50, "max_subdomains": 4},
        "attachment": {"max_count": 25, "max_size_bytes": 10 * 1024 * 1024},
    }
    engine = SecurityEngine(config, StubPhishing(label, score), StubPriority())
    service = AnalysisService(engine)
    settings = Settings(environment="test", auth_mode="required", api_key=api_key)
    return TestClient(create_app(settings, service)), api_key


BODY = {
    "message_id": "m1",
    "sender": "sender@example.com",
    "recipients": ["user@example.com"],
    "subject": "Hello",
    "text_body": "team meeting tomorrow",
    "html_body": "",
    "headers": {},
    "attachments": [],
}


def test_health_public():
    client, _ = make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_failure_and_success():
    client, key = make_client()
    assert client.post("/api/v1/analyze", json=BODY).status_code == 401
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key})
    assert response.status_code == 200


def test_non_phishing_receives_priority():
    client, key = make_client()
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key})
    data = response.json()
    assert data["security"]["classification"] == "NON-PHISHING"
    assert data["priority"]["label"] == "P2"


def test_phishing_suppresses_priority():
    client, key = make_client(label=1, score=2.0)
    body = dict(BODY, headers={"authentication-results": "spf=fail"})
    response = client.post("/api/v1/analyze", json=body, headers={"X-API-Key": key})
    data = response.json()
    assert data["security"]["classification"] == "PHISHING"
    assert data["priority"] is None


def test_suspicious_suppresses_priority():
    client, key = make_client(label=1, score=0.2)
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key})
    data = response.json()
    assert data["security"]["classification"] == "SUSPICIOUS"
    assert data["priority"] is None


def test_review_required_suppresses_priority():
    config = {
        "phishing": {"strong_score_threshold": 1.0, "suspicious_score_threshold": 0.0, "supporting_high_signals": 1},
        "suspicious": {"minimum_meaningful_signals": 1},
        "require_phishing_model": True,
        "url": {"max_length": 2048, "max_count": 50, "max_subdomains": 4},
    }
    service = AnalysisService(SecurityEngine(config))
    settings = Settings(environment="test", auth_mode="required", api_key="test-secret")
    client = TestClient(create_app(settings, service))
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": "test-secret"})
    assert response.status_code == 200
    assert response.json()["security"]["classification"] == "REVIEW REQUIRED"
    assert response.json()["priority"] is None


def test_validation_for_extra_fields_and_missing_required():
    client, key = make_client()
    assert client.post("/api/v1/analyze", json=dict(BODY, unexpected="x"), headers={"X-API-Key": key}).status_code == 422
    invalid = dict(BODY)
    del invalid["sender"]
    assert client.post("/api/v1/analyze", json=invalid, headers={"X-API-Key": key}).status_code == 422


def test_oversized_request_and_request_id():
    client, key = make_client()
    settings = Settings(environment="test", auth_mode="required", api_key=key, max_request_bytes=100)
    service = AnalysisService(SecurityEngine({
        "phishing": {"strong_score_threshold": 1.0, "suspicious_score_threshold": 0.0},
        "suspicious": {"minimum_meaningful_signals": 1},
        "require_phishing_model": True,
    }))
    small_client = TestClient(create_app(settings, service))
    response = small_client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key})
    assert response.status_code == 413

    client, key = make_client()
    response = client.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key, "X-Request-ID": "req-123"})
    assert response.status_code == 200
    assert response.json()["request_id"] == "req-123"


def test_safe_internal_error_does_not_leak_details():
    client, key = make_client()
    class BrokenService:
        def analyze(self, *args):
            raise RuntimeError("/secret/internal/path")
    settings = Settings(environment="test", auth_mode="required", api_key=key)
    broken = TestClient(create_app(settings, BrokenService()))
    response = broken.post("/api/v1/analyze", json=BODY, headers={"X-API-Key": key})
    assert response.status_code == 500
    assert "/secret/internal/path" not in response.text


def test_ready_reports_model_blockers_when_artifacts_unavailable():
    settings = Settings(environment="test", auth_mode="required", api_key="test-secret")
    service = AnalysisService(SecurityEngine({"phishing": {"strong_score_threshold": 1.0, "suspicious_score_threshold": 0.0}, "suspicious": {"minimum_meaningful_signals": 1}, "require_phishing_model": True}))
    client = TestClient(create_app(settings, service))
    response = client.get("/ready")
    assert response.status_code == 503
    assert "phishing_model_unavailable" in response.json()["blockers"]
