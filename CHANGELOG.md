# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to follow [Semantic Versioning](https://semver.org/).

Every commit that changes behavior, configuration, tooling, or documentation adds an entry under `[Unreleased]`. Decisions behind changes are recorded in [docs/adr](docs/adr/README.md).

## [Unreleased]

### Added

- Prometheus metrics at `GET /metrics` ([prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)): request counts and latency per route template; `METRICS_ENABLED` setting; health probes and `/metrics` excluded; Python runtime metrics and, on Linux, process CPU/memory/file-descriptor metrics. ADR-0005 (metrics part).
- Request correlation IDs ([asgi-correlation-id](https://github.com/snok/asgi-correlation-id)): every response has `X-Request-ID` (inbound UUIDs are kept) and every log line during a request carries `request_id`.
- Structured JSON logging with [structlog](https://www.structlog.org/): stdlib and uvicorn logs share one format; `LOG_LEVEL` and `LOG_JSON` settings; `app_started`, `app_stopping`, `documents_ingested` and `query_answered` events that carry counts only. ADR-0005 (logging part).
- Architecture Decision Records in `docs/adr/` (index, template, and ADR-0001).
- This changelog.
- [ruff](https://docs.astral.sh/ruff/) for linting and formatting (rules E, F, I, B, UP, S, D with Google docstring style; line length 100), added to the dev group. The docstring rule is now machine-checked. `D100` (module docstrings) is ignored because the project rules do not require them; `assert` is allowed in tests.
- [pre-commit](https://pre-commit.com/) config (whitespace/YAML/TOML hooks plus locked `ruff` and `mypy`) and [pip-audit](https://github.com/pypa/pip-audit) in the dev group. README documents usage and the currently unfixed `chromadb` advisories (server-side only).

- `GET /health/live` and `GET /health/ready` (503 with a reason list when the API key is missing or the vector store is unreachable); `GET /health` remains as an alias of live.
- `VectorStore.ping()` (Chroma heartbeat; returns False instead of raising), used by `/health/ready`.
- ADR-0004 (config, lifespan, health), a README Configuration table, and a README health section; `.env.example` lists every optional setting.

### Changed

- Services are now created in a FastAPI lifespan and closed on shutdown (OpenAI client and `VectorStore.close()`, new in the protocol). They exist only while the app runs; tests must use `with TestClient(app)`.
- Settings now use [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): all fields can be set via environment variables or `.env`, limits are validated at startup, and `openai_api_key` is a `SecretStr` that never appears in `repr`. `load_settings()` and the direct `python-dotenv` dependency are removed.
- Project rules ([ADR-0002](docs/adr/0002-relax-dependency-and-infrastructure-rules.md)): prefer maintained libraries over hand-written code; LangChain/LlamaIndex allowed per component with an ADR (the RAG pipeline stays explicit); Docker and a Chroma server container allowed; added a Process section (ADRs, one logical commit, CHANGELOG, commit format). Auth, rate limiting, and managed databases remain out of scope until deployment.
- `DESIGN.md` non-goals and future work updated to match.
- ADR conventions now ask for concise records (about 15 lines); the template is shorter.
- Dependency management moved to [uv](https://docs.astral.sh/uv/) with a committed `uv.lock` ([ADR-0003](docs/adr/0003-use-uv-ruff-and-pre-commit.md)). Setup is now `uv sync`; dev tools moved to `[dependency-groups]`, so `pip install -e ".[dev]"` no longer applies.
- `requires-python` is now `>=3.11,<3.14` so the universal lockfile resolves on Intel macOS (newer `onnxruntime` wheels are missing there).
- Locked dependency versions are newer than the previous unpinned install (for example FastAPI 0.162, OpenAI SDK 3.42, pydantic 2.14); the test suite and `mypy --strict` pass with them.
- README now documents `uv add` as the way to change dependencies.

### Fixed

- Three docstring lines over 100 characters shortened (found by the new ruff config; no behavior change).
- Python upper bound corrected from `<3.15` to `<3.14`. The first uv lock did not re-resolve, so it missed that Python 3.14 has no Intel-macOS `onnxruntime` wheel; `uv add`/`uv lock --upgrade` failed until the bound was lowered. No package versions changed.

## [0.1.0] - 2026-10-14

Initial version, before the production-readiness work.

### Added

- FastAPI service with `GET /health`, `POST /documents`, `GET /documents`, `DELETE /documents/{document_id}`, and `POST /query`.
- RAG pipeline on the native OpenAI SDK (`gpt-4o-mini`, `text-embedding-3-small`) and a local persistent ChromaDB store.
- PDF, Markdown, and plain-text ingestion with heading- and paragraph-aware chunking.
- Typed code (`mypy --strict`), docstrings on all functions and classes, and a mocked pytest suite that never calls the live API.
- `DESIGN.md` and `PROJECT_RULES.md`.
