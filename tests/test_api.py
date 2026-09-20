"""Tests for bootstrap API routes."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    """The health route exposes the required status response."""
    assert client.get("/health").json() == {"status": "ok"}


def test_troubleshoot_returns_placeholder() -> None:
    """The bootstrap route must not pretend to have a real plan."""
    response = client.post("/api/v1/troubleshoot", json={"query": "Example issue"})
    assert response.status_code == 200
    assert response.json()["status"] == "placeholder"
