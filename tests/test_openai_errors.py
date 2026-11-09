import json

import httpx2
import openai
import pytest

from tests.conftest import AppFactory
from tests.http import client_for

UPSTREAM_TEXT = "upstream-detail-sk-leak-check"
_REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/embeddings")


def _response(status_code: int, headers: dict[str, str] | None = None) -> httpx2.Response:
    """A real response of the type the OpenAI SDK (httpx2) attaches to status errors."""
    return httpx2.Response(status_code, request=_REQUEST, headers=headers)


class RaisingEmbedder:
    """Embedder that raises a given exception, to drive the error handlers."""

    def __init__(self, exc: Exception) -> None:
        """Remember the exception to raise."""
        self.exc = exc

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Raise the configured exception instead of embedding."""
        raise self.exc


CASES = [
    pytest.param(
        openai.RateLimitError(
            UPSTREAM_TEXT, response=_response(429, {"retry-after": "7"}), body=None
        ),
        503,
        "OpenAI rate limit reached; retry later",
        {"retry-after": "7"},
        id="rate-limit",
    ),
    pytest.param(
        openai.APITimeoutError(request=_REQUEST),
        504,
        "OpenAI request timed out",
        {},
        id="timeout",
    ),
    pytest.param(
        openai.APIConnectionError(message=UPSTREAM_TEXT, request=_REQUEST),
        502,
        "OpenAI request failed",
        {},
        id="connection",
    ),
    pytest.param(
        openai.AuthenticationError(UPSTREAM_TEXT, response=_response(401), body=None),
        503,
        "Upstream service is misconfigured",
        {},
        id="authentication",
    ),
    pytest.param(
        openai.PermissionDeniedError(UPSTREAM_TEXT, response=_response(403), body=None),
        503,
        "Upstream service is misconfigured",
        {},
        id="permission",
    ),
    pytest.param(
        openai.BadRequestError(UPSTREAM_TEXT, response=_response(400), body=None),
        502,
        "OpenAI request failed",
        {},
        id="bad-request",
    ),
    pytest.param(
        openai.InternalServerError(UPSTREAM_TEXT, response=_response(500), body=None),
        502,
        "OpenAI request failed",
        {},
        id="server-error",
    ),
    pytest.param(
        openai.OpenAIError(UPSTREAM_TEXT),
        502,
        "OpenAI request failed",
        {},
        id="generic",
    ),
]


@pytest.mark.parametrize(("exc", "status_code", "detail", "headers"), CASES)
def test_openai_errors_map_to_precise_status(
    make_app: AppFactory,
    exc: Exception,
    status_code: int,
    detail: str,
    headers: dict[str, str],
) -> None:
    """Each OpenAI failure maps to its documented status, message and headers."""
    with client_for(make_app(embedder=RaisingEmbedder(exc))) as client:
        response = client.post("/query", json={"question": "hello"})

    assert response.status_code == status_code
    assert response.json()["detail"] == detail
    for name, value in headers.items():
        assert response.headers[name] == value
    assert UPSTREAM_TEXT not in response.text


def test_retry_after_falls_back_when_upstream_omits_it(make_app: AppFactory) -> None:
    """Without a usable upstream `retry-after`, a default is still sent."""
    exc = openai.RateLimitError("limited", response=_response(429), body=None)
    with client_for(make_app(embedder=RaisingEmbedder(exc))) as client:
        response = client.post("/query", json={"question": "hello"})

    assert response.status_code == 503
    assert int(response.headers["retry-after"]) > 0


def test_credential_errors_are_logged_at_error_without_upstream_text(
    make_app: AppFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    """Credential failures need an operator: error level, type and status, no message."""
    exc = openai.AuthenticationError(UPSTREAM_TEXT, response=_response(401), body=None)
    with client_for(make_app(embedder=RaisingEmbedder(exc))) as client:
        client.post("/query", json={"question": "hello"})

    output = capsys.readouterr().out
    lines = [json.loads(line) for line in output.splitlines() if line.strip()]
    failure = next(line for line in lines if line["event"] == "openai_request_failed")
    assert failure["level"] == "error"
    assert failure["error_type"] == "AuthenticationError"
    assert failure["upstream_status"] == 401
    assert UPSTREAM_TEXT not in output
