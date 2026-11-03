# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to follow [Semantic Versioning](https://semver.org/).

Every commit that changes behavior, configuration, tooling, or documentation adds an entry under `[Unreleased]`. Decisions behind changes are recorded in [docs/adr](docs/adr/README.md).

## [Unreleased]

### Added

- Architecture Decision Records in `docs/adr/` (index, template, and ADR-0001).
- This changelog.

### Changed

- Project rules ([ADR-0002](docs/adr/0002-relax-dependency-and-infrastructure-rules.md)): prefer maintained libraries over hand-written code; LangChain/LlamaIndex allowed per component with an ADR (the RAG pipeline stays explicit); Docker and a Chroma server container allowed; added a Process section (ADRs, one logical commit, CHANGELOG, commit format). Auth, rate limiting, and managed databases remain out of scope until deployment.
- `DESIGN.md` non-goals and future work updated to match.
- ADR conventions now ask for concise records (about 15 lines); the template is shorter.
- Dependency management moved to [uv](https://docs.astral.sh/uv/) with a committed `uv.lock` ([ADR-0003](docs/adr/0003-use-uv-ruff-and-pre-commit.md)). Setup is now `uv sync`; dev tools moved to `[dependency-groups]`, so `pip install -e ".[dev]"` no longer applies.
- `requires-python` is now `>=3.11,<3.15` so the universal lockfile resolves on Intel macOS (newer `onnxruntime` wheels are missing there).
- Locked dependency versions are newer than the previous unpinned install (for example FastAPI 0.162, OpenAI SDK 3.42, pydantic 2.14); the test suite and `mypy --strict` pass with them.

## [0.1.0] - 2026-10-14

Initial version, before the production-readiness work.

### Added

- FastAPI service with `GET /health`, `POST /documents`, `GET /documents`, `DELETE /documents/{document_id}`, and `POST /query`.
- RAG pipeline on the native OpenAI SDK (`gpt-4o-mini`, `text-embedding-3-small`) and a local persistent ChromaDB store.
- PDF, Markdown, and plain-text ingestion with heading- and paragraph-aware chunking.
- Typed code (`mypy --strict`), docstrings on all functions and classes, and a mocked pytest suite that never calls the live API.
- `DESIGN.md` and `PROJECT_RULES.md`.
