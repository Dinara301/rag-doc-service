# General Project Rules

- Python 3.11+, strict type annotations everywhere.
- Use FastAPI with Pydantic v2 for request/response validation.
- Follow Clean Architecture: Keep API routes thin (thin controllers), put business/RAG logic in `app/rag/`, and storage abstraction in `app/storage/`.

# Documentation

- Every function, method, nested function, and class MUST have a docstring. This includes private helpers (`_name`), Protocol methods, Pydantic models, dataclasses, test functions, test fakes, and pytest fixtures. Add or update the docstring in the same change that adds or modifies the code.
- Use triple double quotes. Start with a concise one-line summary in the imperative mood ("Return...", "Split..."), ending with a period.
- Add more detail only when it is not obvious from the signature: behavior, units, side effects, and a `Raises:` section listing the exceptions callers should expect. Do not restate parameter types (they are in the annotations).
- Docstrings on FastAPI route functions appear as endpoint descriptions in the OpenAPI docs, so write them for API consumers.
- Test docstrings state the behavior being verified, not how.
- Keep docstrings accurate: if code changes, update its docstring.

# RAG & Dependencies

- DO NOT use LangChain or LlamaIndex. Write clean, explicit RAG pipelines using native OpenAI SDK and ChromaDB SDK directly.
- Use `gpt-4o-mini` for LLM generation and `text-embedding-3-small` for embeddings.
- Vector DB: Use local persistent ChromaDB stored at `data/chroma/`.

# Testing & Code Quality

- All tests must use `pytest` and `httpx`.
- Mock OpenAI calls in unit/integration tests (no live API calls during pytest).
- Keep codebase minimalistic and self-contained for v1 (no Docker, no auth, no external DBs yet).
