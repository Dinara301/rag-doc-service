from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from openai import OpenAIError

from app.api.schemas import ErrorResponse
from app.rag.loaders import DocumentRejectedError


def _error(status_code: int, detail: str) -> JSONResponse:
    """Build a JSON error response shaped like `ErrorResponse`."""
    return JSONResponse(status_code=status_code, content=ErrorResponse(detail=detail).model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain and upstream errors to HTTP responses so routes stay free of try/except."""

    @app.exception_handler(DocumentRejectedError)
    async def handle_rejected_document(_: Request, exc: DocumentRejectedError) -> JSONResponse:
        """Return 400 with the rejection reason for files that cannot be ingested."""
        return _error(status.HTTP_400_BAD_REQUEST, str(exc))

    @app.exception_handler(OpenAIError)
    async def handle_openai_error(_: Request, exc: OpenAIError) -> JSONResponse:
        """Return 502 with a generic message; the upstream error text is not exposed."""
        return _error(status.HTTP_502_BAD_GATEWAY, "OpenAI request failed")
