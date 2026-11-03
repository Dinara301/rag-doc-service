# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to follow [Semantic Versioning](https://semver.org/).

Every commit that changes behavior, configuration, tooling, or documentation adds an entry under `[Unreleased]`. Decisions behind changes are recorded in [docs/adr](docs/adr/README.md).

## [Unreleased]

### Added

- Architecture Decision Records in `docs/adr/` (index, template, and ADR-0001).
- This changelog.

## [0.1.0] - 2026-10-14

Initial version, before the production-readiness work.

### Added

- FastAPI service with `GET /health`, `POST /documents`, `GET /documents`, `DELETE /documents/{document_id}`, and `POST /query`.
- RAG pipeline on the native OpenAI SDK (`gpt-4o-mini`, `text-embedding-3-small`) and a local persistent ChromaDB store.
- PDF, Markdown, and plain-text ingestion with heading- and paragraph-aware chunking.
- Typed code (`mypy --strict`), docstrings on all functions and classes, and a mocked pytest suite that never calls the live API.
- `DESIGN.md` and `PROJECT_RULES.md`.
