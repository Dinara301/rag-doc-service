from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from openai import OpenAIError

from app.api.schemas import ErrorResponse
from app.rag.loaders import DocumentRejectedError


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(detail=detail).model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentRejectedError)
    async def handle_rejected_document(_: Request, exc: DocumentRejectedError) -> JSONResponse:
        return _error(status.HTTP_400_BAD_REQUEST, str(exc))

    @app.exception_handler(OpenAIError)
    async def handle_openai_error(_: Request, exc: OpenAIError) -> JSONResponse:
        return _error(status.HTTP_502_BAD_GATEWAY, "OpenAI request failed")
