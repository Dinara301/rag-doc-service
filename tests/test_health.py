import pytest
from fastapi import FastAPI

from tests.conftest import AppFactory
from tests.http import client_for


@pytest.mark.parametrize("path", ["/health", "/health/live"])
def test_live_returns_ok(app: FastAPI, path: str) -> None:
    """`/health/live` and its `/health` alias return 200 with status ok."""
    with client_for(app) as client:
        response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_live_ignores_dependency_failures(
    make_app: AppFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Liveness stays 200 even with no API key and a dead store."""
    app = make_app(api_key="")
    with client_for(app) as client:
        monkeypatch.setattr(app.state.services.vector_store, "ping", lambda: False)
        assert client.get("/health/live").status_code == 200


def test_ready_returns_ok_when_configured(app: FastAPI) -> None:
    """With a key and a healthy store the service is ready."""
    with client_for(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "reasons": []}


def test_ready_is_503_without_api_key(make_app: AppFactory) -> None:
    """A missing API key makes the service not ready, with a reason."""
    with client_for(make_app(api_key="")) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "reasons": ["OPENAI_API_KEY is not configured"],
    }


def test_ready_is_503_when_store_ping_fails(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unreachable vector store makes the service not ready, with a reason."""
    with client_for(app) as client:
        monkeypatch.setattr(app.state.services.vector_store, "ping", lambda: False)
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "reasons": ["vector store is unreachable"],
    }
