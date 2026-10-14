from fastapi import FastAPI

from tests.http import client_for


def test_health_returns_ok(app: FastAPI) -> None:
    """GET /health returns 200 with status ok."""
    with client_for(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
