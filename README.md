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

Use `uv run <command>` to run anything inside the environment (or `source .venv/bin/activate`). To change dependencies, edit `pyproject.toml` and run `uv lock`.

## Run

```bash
uv run uvicorn app.main:create_app --factory --reload
```

The app is built by a factory, so importing `app.main` has no side effects (no `data/` created).

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
