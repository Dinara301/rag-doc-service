# General Project Rules

- Python 3.11+, strict type annotations everywhere.
- Use FastAPI with Pydantic v2 for request/response validation.
- Follow Clean Architecture: Keep API routes thin (thin controllers), put business/RAG logic in `app/rag/`, and storage abstraction in `app/storage/`.

# RAG & Dependencies

- DO NOT use LangChain or LlamaIndex. Write clean, explicit RAG pipelines using native OpenAI SDK and ChromaDB SDK directly.
- Use `gpt-4o-mini` for LLM generation and `text-embedding-3-small` for embeddings.
- Vector DB: Use local persistent ChromaDB stored at `data/chroma/`.

# Testing & Code Quality

- All tests must use `pytest` and `httpx`.
- Mock OpenAI calls in unit/integration tests (no live API calls during pytest).
- Keep codebase minimalistic and self-contained for v1 (no Docker, no auth, no external DBs yet).
