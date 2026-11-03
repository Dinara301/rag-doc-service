# General Project Rules

- Python 3.11+ (currently capped below 3.14 by dependency wheel availability, see ADR-0003), strict type annotations everywhere.
- Manage dependencies with `uv`; commit `uv.lock` and update it with every dependency change.
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

- Prefer well-maintained libraries over hand-written code for solved problems (configuration, retries, text splitting, logging, metrics). Write custom code only when no library fits or a library would hide behavior we need to control, and say why in the commit or an ADR.
- LangChain, LlamaIndex, and similar frameworks are allowed only for a specific component, and only when an ADR shows the benefit over a focused library. The RAG pipeline itself stays explicit: native OpenAI SDK and ChromaDB client, behind the `Embedder`, `AnswerGenerator`, and `VectorStore` protocols.
- Use `gpt-4o-mini` for LLM generation and `text-embedding-3-small` for embeddings.
- Vector DB: ChromaDB, accessed only through `app/storage/`. It runs embedded (local `data/chroma/`) for development and tests, and as a separate Chroma server container (HTTP client) for production-like runs. Managed or hosted vector databases are out of scope.

# Testing & Code Quality

- All tests must use `pytest` and `httpx`.
- Mock OpenAI calls in unit/integration tests (no live API calls during pytest).
- Keep the codebase minimal. Docker images and compose files are allowed. Authentication, rate limiting, and managed or hosted databases stay out of scope until the deployment stage.

# Process

- Record decisions that have real alternatives as ADRs in `docs/adr/` (see `docs/adr/README.md`), in the same change or the commit just before it.
- Make one logical change per commit. Each commit updates tests, docs, and `CHANGELOG.md` (`[Unreleased]`), and leaves every configured check green (currently `pytest` and `mypy --strict`).
- Use a Conventional Commits subject (`type(scope): summary`). Put `Why`, `What`, `Tests`, `Docs`, and (when relevant) `ADR` lines in the body.
