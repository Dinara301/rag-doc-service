# doc-qa-api

REST API RAG service: upload tech docs (PDF, Markdown, TXT) and ask questions. Answers are JSON with citations.

Project rules: [PROJECT_RULES.md](PROJECT_RULES.md). Design: [DESIGN.md](DESIGN.md).

## Setup

Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# set OPENAI_API_KEY in .env
```

## Run

```bash
uvicorn app.main:create_app --factory --reload
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
pytest
mypy          # strict type check (required by PROJECT_RULES.md)
```
