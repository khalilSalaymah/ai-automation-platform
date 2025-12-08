"""Tests for email agent application."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "email-agent"

