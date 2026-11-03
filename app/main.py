from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from openai import OpenAI

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.config import Settings
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
    """Build the FastAPI application; services are created at startup and closed at shutdown.

    Every argument is optional: `settings` defaults to `Settings()`, and the vector store,
    embedder and generator default to the Chroma/OpenAI implementations. Tests pass fakes to
    avoid live API calls. The app takes ownership of a `vector_store` passed in and closes it
    on shutdown. Services exist only while the lifespan is running, so use the app as a context
    manager in tests (`with TestClient(app)`).

    Run with: ``uvicorn app.main:create_app --factory --reload``
    """
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Build `AppServices` on startup and release their resources on shutdown."""
        async with AsyncExitStack() as stack:
            store = vector_store or ChromaVectorStore(resolved.chroma_path)
            stack.callback(store.close)

            resolved_embedder, resolved_generator = embedder, generator
            if resolved_embedder is None or resolved_generator is None:
                client = OpenAI(
                    api_key=resolved.openai_api_key.get_secret_value() or _UNCONFIGURED_API_KEY
                )
                stack.callback(client.close)
                resolved_embedder = resolved_embedder or OpenAIEmbedder(
                    client, resolved.embedding_model
                )
                resolved_generator = resolved_generator or OpenAIAnswerGenerator(
                    client, resolved.chat_model
                )

            app.state.services = AppServices(
                settings=resolved,
                vector_store=store,
                embedder=resolved_embedder,
                generator=resolved_generator,
            )
            yield
            del app.state.services

    app = FastAPI(title="doc-qa-api", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    register_exception_handlers(app)
    return app
