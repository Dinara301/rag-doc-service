from dataclasses import dataclass, field

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from openai import (
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from app.api.schemas import ErrorResponse
from app.rag.loaders import DocumentRejectedError

# Used when OpenAI does not send a usable `retry-after` (seconds) with a rate-limit error.
DEFAULT_RETRY_AFTER_SECONDS: int = 10

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class MappedError:
    """HTTP status, client-safe message and extra headers for an upstream failure."""

    status_code: int
    detail: str
    headers: dict[str, str] = field(default_factory=dict)


def _error(status_code: int, detail: str, headers: dict[str, str] | None = None) -> JSONResponse:
    """Build a JSON error response shaped like `ErrorResponse`."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
        headers=headers,
    )


def _retry_after_seconds(exc: RateLimitError) -> int:
    """Read OpenAI's `retry-after` header in whole seconds, or fall back to the default."""
    raw = exc.response.headers.get("retry-after", "")
    try:
        seconds = int(float(raw))
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS
    return seconds if seconds > 0 else DEFAULT_RETRY_AFTER_SECONDS


def map_openai_error(exc: OpenAIError) -> MappedError:
    """Translate an OpenAI SDK error into a response; upstream text is never included.

    The policy is recorded in ADR-0006: rate limits and our own credential problems are 503
    (the caller did not cause them), timeouts are 504, everything else is 502.
    """
    if isinstance(exc, RateLimitError):
        return MappedError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OpenAI rate limit reached; retry later",
            {"Retry-After": str(_retry_after_seconds(exc))},
        )
    if isinstance(exc, AuthenticationError | PermissionDeniedError):
        return MappedError(status.HTTP_503_SERVICE_UNAVAILABLE, "Upstream service is misconfigured")
    if isinstance(exc, APITimeoutError):
        return MappedError(status.HTTP_504_GATEWAY_TIMEOUT, "OpenAI request timed out")
    return MappedError(status.HTTP_502_BAD_GATEWAY, "OpenAI request failed")


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain and upstream errors to HTTP responses so routes stay free of try/except."""

    @app.exception_handler(DocumentRejectedError)
    async def handle_rejected_document(_: Request, exc: DocumentRejectedError) -> JSONResponse:
        """Return 400 with the rejection reason for files that cannot be ingested."""
        return _error(status.HTTP_400_BAD_REQUEST, str(exc))

    @app.exception_handler(OpenAIError)
    async def handle_openai_error(_: Request, exc: OpenAIError) -> JSONResponse:
        """Return the mapped status and generic message, and log the failure without its text.

        Credential errors are logged at error level because they need an operator.
        """
        mapped = map_openai_error(exc)
        upstream_status = exc.status_code if isinstance(exc, APIStatusError) else None
        is_credentials = isinstance(exc, AuthenticationError | PermissionDeniedError)
        (log.error if is_credentials else log.warning)(
            "openai_request_failed",
            error_type=type(exc).__name__,
            upstream_status=upstream_status,
            status_code=mapped.status_code,
        )
        return _error(mapped.status_code, mapped.detail, mapped.headers or None)
