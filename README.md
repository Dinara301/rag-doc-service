# doc-qa-api

REST API RAG service: upload tech docs (PDF, Markdown, TXT) and ask questions. Answers are JSON with citations.

Project rules: [PROJECT_RULES.md](PROJECT_RULES.md). Design: [DESIGN.md](DESIGN.md).

## Decisions and changes

- Decisions with real alternatives are recorded as ADRs in [docs/adr](docs/adr/README.md).
- Every change is listed in [CHANGELOG.md](CHANGELOG.md).
- Commit messages follow Conventional Commits and carry `Why`, `What`, `Tests`, `Docs`, and (when relevant) `ADR` lines in the body.

## Setup

Python 3.11 to 3.13. Dependencies are managed with [uv](https://docs.astral.sh/uv/getting-started/installation/) and pinned in `uv.lock`.

```bash
uv sync                  # creates .venv from uv.lock (runtime + dev tools)
cp .env.example .env
# set OPENAI_API_KEY in .env
```

Use `uv run <command>` to run anything inside the environment (or `source .venv/bin/activate`). To change dependencies use `uv add <pkg>` (or `uv add --dev <pkg>`), which updates `pyproject.toml` and `uv.lock` together; commit both.

## Configuration

Settings come from environment variables or a local `.env` file ([pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/), [ADR-0004](docs/adr/0004-config-lifespan-and-health.md)). Invalid values stop startup with a validation error; the API key is never printed.

| Variable | Default | Meaning |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | Required for ingest and query (503 without it) |
| `CHAT_MODEL` | `gpt-4o-mini` | Answer model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHROMA_PATH` | `data/chroma` | Embedded Chroma directory |
| `CHUNK_SIZE_TOKENS` | `800` | Approximate chunk size |
| `CHUNK_OVERLAP_TOKENS` | `150` | Approximate chunk overlap |
| `MAX_FILE_BYTES` | `10485760` | Per-file upload limit |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |
| `LOG_JSON` | `true` | JSON lines on stdout; `false` for readable console output in development |
| `METRICS_ENABLED` | `true` | Expose Prometheus metrics at `/metrics` |
| `ALLOWED_EXTENSIONS` | `[".pdf", ".md", ".markdown", ".txt"]` (JSON list) | Accepted file types |

## Run

```bash
uv run uvicorn app.main:create_app --factory --reload
```

The app is built by a factory, so importing `app.main` has no side effects (no `data/` created).

Health endpoints: `GET /health/live` (alias `/health`) answers 200 while the process is up and never checks dependencies; `GET /health/ready` answers 200 when the API key is set and the vector store responds, otherwise 503 with a list of `reasons`. Use live for restarts and ready for traffic routing.

## Logging

Logs are written to stdout as one JSON object per line (`timestamp`, `level`, `logger`, `event`, plus fields). Our logs, stdlib logs and uvicorn's logs share this format ([ADR-0005](docs/adr/0005-observability-stack.md)). Set `LOG_JSON=false` for readable output while developing. The service logs counts and ids only (for example `documents_ingested` with `document_count` and `chunk_count`); API keys, file contents, filenames and questions are never logged.

Every response carries an `X-Request-ID` header, and every log line written during that request has the same `request_id`. Send your own `X-Request-ID` (a UUID, dashed or 32-hex) to trace a call across services; anything else is replaced with a generated ID.

## Operations

`GET /metrics` serves Prometheus metrics ([ADR-0005](docs/adr/0005-observability-stack.md)); set `METRICS_ENABLED=false` to turn it off. Main series: `http_requests_total{handler,method,status}` (status grouped as `2xx`, `4xx`, `5xx`), `http_request_duration_seconds{handler,method}` (buckets up to 30s) request/response size summaries, and runtime metrics (`python_gc_*`, `python_info`, plus `process_*` CPU, memory and file descriptors on Linux). `handler` is the route template, for example `/documents/{document_id}`, so label cardinality stays bounded. Health probes and `/metrics` are not counted.

`/metrics` has no authentication: expose it only on a private network. Counters are per instance, so scrape every replica.

## Example

Upload:

```bash
curl -s -X POST http://127.0.0.1:8000/documents \
  -F "files=@README.md"
```

Query:

```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What does this service do?","top_k":5}'
```

## Tests

Tests mock OpenAI (hash embeddings + fake generator). They never call the live API.

```bash
uv run pytest
```

## Quality checks

All of these must pass before every commit:

```bash
uv run ruff check            # lint (also enforces the docstring rule)
uv run ruff format --check   # formatting; run `uv run ruff format` to fix
uv run mypy                  # strict type check (required by PROJECT_RULES.md)
uv run pytest
```

Optional, but recommended: run the same checks (plus whitespace/YAML/TOML hooks) automatically on `git commit`:

```bash
uv run pre-commit install          # once per clone
uv run pre-commit run --all-files  # run manually
```

Audit dependencies for known vulnerabilities (needs network):

```bash
uv run pip-audit
```

Known findings (2026-11-03): `chromadb 1.5.9` has 5 advisories with no fixed release yet (PYSEC-2026-311, -3813, -3814, -3815). They concern the Chroma HTTP server (remote model loading, RBAC/tenant checks). The current embedded mode with OpenAI embeddings does not expose them; when Chroma runs as a server (Plan 06), keep it on a private network and do not enable its auth providers or remote-code options.

Ruff is configured in `pyproject.toml` (line length 100; rules E, F, I, B, UP, S, D with Google docstring style). Module docstrings (`D100`) are not required, matching `PROJECT_RULES.md`; `assert` is allowed in tests.
