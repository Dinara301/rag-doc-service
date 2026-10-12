from fastapi import FastAPI
from openai import OpenAI

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.config import Settings, load_settings
from app.dependencies import AppServices
from app.rag.llm import AnswerGenerator, Embedder, OpenAIAnswerGenerator, OpenAIEmbedder
from app.storage.vector_store import ChromaVectorStore, VectorStore

# Placeholder so the app can start (and serve /health, /documents) without a key;
# OpenAI-backed routes return 503 until OPENAI_API_KEY is configured.
_UNCONFIGURED_API_KEY: str = "unconfigured"


def create_app(
    settings: Settings | None = None,
    *,
    vector_store: VectorStore | None = None,
    embedder: Embedder | None = None,
    generator: AnswerGenerator | None = None,
) -> FastAPI:
    """App factory. Run with: uvicorn app.main:create_app --factory --reload"""
    resolved = settings or load_settings()

    if embedder is None or generator is None:
        client = OpenAI(api_key=resolved.openai_api_key or _UNCONFIGURED_API_KEY)
        embedder = embedder or OpenAIEmbedder(client, resolved.embedding_model)
        generator = generator or OpenAIAnswerGenerator(client, resolved.chat_model)

    app = FastAPI(title="doc-qa-api", version="0.1.0")
    app.state.services = AppServices(
        settings=resolved,
        vector_store=vector_store or ChromaVectorStore(resolved.chroma_path),
        embedder=embedder,
        generator=generator,
    )
    app.include_router(router)
    register_exception_handlers(app)
    return app
