import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import AppFactory, FailingEmbedder
from tests.http import client_for

INTERNAL_DETAIL = "kaboom-internal-detail"


def _add_failing_route(app: FastAPI) -> None:
    """Register a route that raises an unexpected exception."""

    def boom() -> None:
        raise RuntimeError(INTERNAL_DETAIL)

    app.add_api_route("/boom", boom)


def test_unexpected_error_returns_safe_json_500_with_request_id(make_app: AppFactory) -> None:
    """Unhandled exceptions become a generic JSON 500 whose `request_id` matches the header."""
    app = make_app()
    _add_failing_route(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert INTERNAL_DETAIL not in response.text
    assert "Traceback" not in response.text


def test_unexpected_error_keeps_an_inbound_request_id(make_app: AppFactory) -> None:
    """A caller-supplied ID is reported back on 500s too, so the caller can quote it."""
    app = make_app()
    _add_failing_route(app)
    inbound = "4ede32b925734861abd48c8b03ca8b41"
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={"X-Request-ID": inbound})

    assert response.json()["request_id"] == inbound
    assert response.headers.get_list("X-Request-ID") == [inbound]


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "status_code"),
    [
        ("DELETE", "/documents/unknown", {}, 404),
        ("POST", "/query", {"json": {"question": "hi"}}, 503),
    ],
    ids=["not-found", "missing-api-key"],
)
def test_http_exceptions_include_request_id_once(
    make_app: AppFactory,
    method: str,
    path: str,
    kwargs: dict[str, object],
    status_code: int,
) -> None:
    """404 and 503 bodies carry `request_id`, and the header is not duplicated."""
    with client_for(make_app(api_key="")) as client:
        response = client.request(method, path, **kwargs)  # type: ignore[arg-type]

    assert response.status_code == status_code
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert len(response.headers.get_list("X-Request-ID")) == 1


def test_mapped_openai_error_includes_request_id(make_app: AppFactory) -> None:
    """Mapped upstream errors (502 here) also carry the ID."""
    with client_for(make_app(embedder=FailingEmbedder())) as client:
        response = client.post("/query", json={"question": "hello"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "OpenAI request failed",
        "request_id": response.headers["X-Request-ID"],
    }


def test_validation_errors_keep_fastapi_default_body(app: FastAPI) -> None:
    """422 bodies are unchanged (ADR-0006): a list of validation errors, no `request_id`."""
    with client_for(app) as client:
        response = client.post("/query", json={"question": ""})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert "request_id" not in body
