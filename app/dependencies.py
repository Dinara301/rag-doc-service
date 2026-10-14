from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings
from app.rag.llm import AnswerGenerator, Embedder
from app.storage.vector_store import VectorStore


@dataclass
class AppServices:
    """The collaborators routes need, created once in `create_app` and stored on `app.state`."""

    settings: Settings
    vector_store: VectorStore
    embedder: Embedder
    generator: AnswerGenerator


def get_services(request: Request) -> AppServices:
    """FastAPI dependency returning the `AppServices` attached to the running app."""
    services = getattr(request.app.state, "services", None)
    if not isinstance(services, AppServices):
        raise RuntimeError("Application services are not initialized")
    return services


def get_openai_ready_services(
    services: Annotated[AppServices, Depends(get_services)],
) -> AppServices:
    """Services for routes that call OpenAI; fails fast when no API key is configured.

    Raises:
        HTTPException: 503 when `OPENAI_API_KEY` is not set.
    """
    if not services.settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured",
        )
    return services


ServicesDep = Annotated[AppServices, Depends(get_services)]
OpenAIServicesDep = Annotated[AppServices, Depends(get_openai_ready_services)]
