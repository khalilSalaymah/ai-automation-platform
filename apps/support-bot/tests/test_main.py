"""Support-bot tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.support_service import (
    compute_confidence,
    should_escalate,
)
from app.agents.support_agent import simple_intent_classifier
from app.models.support_models import Intent

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "support-bot"


def test_compute_confidence_basic():
    value = compute_confidence(0.8, 0.6)
    assert 0.0 <= value <= 1.0
    assert abs(value - 0.7) < 1e-6


def test_should_escalate_threshold():
    assert should_escalate(0.5, threshold=0.65) is True
    assert should_escalate(0.65, threshold=0.65) is False
    assert should_escalate(0.9, threshold=0.65) is False


def test_simple_intent_classifier_billing():
    intent = simple_intent_classifier("I have a billing issue with my invoice")
    assert intent == Intent.BILLING


def test_simple_intent_classifier_technical():
    intent = simple_intent_classifier("The app throws an error when I login")
    assert intent == Intent.TECHNICAL


def test_simple_intent_classifier_general():
    intent = simple_intent_classifier("Tell me more about your product")
    assert intent == Intent.GENERAL


