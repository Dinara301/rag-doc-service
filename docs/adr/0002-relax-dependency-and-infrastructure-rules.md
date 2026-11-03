# 0002. Relax dependency and infrastructure rules

- Status: Accepted
- Date: 2026-11-03

## Context

`PROJECT_RULES.md` was written for a minimal first version. Three of its rules now block the production-readiness roadmap:

- "DO NOT use LangChain or LlamaIndex." Part of the roadmap replaces hand-written plumbing (for example the text chunker, which guesses tokens as 4 characters) with maintained libraries, and the maintained token-aware Markdown splitter we want ships in the LangChain ecosystem.
- "Use local persistent ChromaDB stored at `data/chroma/`." Embedded Chroma is a single-process store, so several API replicas cannot safely share it. Horizontal scaling needs Chroma as its own server.
- "No Docker, no auth, no external DBs yet." Containerization is in scope; a Chroma server container counts as a separate service.

The project owner confirmed that library choices may be opened up, provided the choice is justified.

## Options considered

1. Remove all restrictions on libraries and frameworks. Fastest, but nothing stops a framework from replacing the explicit pipeline and hiding timeout, retry, and error behavior we are trying to control.
2. Keep the ban and hand-write everything. Keeps the pipeline explicit, but contradicts the goal of using maintained libraries and leaves us maintaining a chunker and other plumbing ourselves.
3. Prefer maintained libraries, allow frameworks only per component with an ADR, and keep the RAG pipeline explicit behind the existing protocols.

## Decision

Use option 3. Concretely:

- Prefer well-maintained libraries over hand-written code for solved problems. Custom code needs a stated reason.
- LangChain, LlamaIndex, and similar are allowed for a specific component only when an ADR shows the benefit over a focused library. The pipeline stays on the native OpenAI SDK and ChromaDB client behind `Embedder`, `AnswerGenerator`, and `VectorStore`.
- Chroma remains the vector store, accessed only through `app/storage/`. Embedded mode stays for development and tests; a Chroma server container is allowed for production-like runs. Managed or hosted vector databases remain out of scope.
- Docker images and compose files are allowed. Authentication, rate limiting, and managed databases stay out of scope until the deployment stage.

## Consequences

- Later plans can adopt libraries (settings, logging, metrics, retries, text splitting) without breaking the rules, each with its ADR where there are real alternatives.
- Keeping the pipeline explicit costs a little code but keeps tests simple (protocol fakes) and error behavior visible.
- `DESIGN.md` non-goals and future-work lines are updated to match.
- A future move to a different vector store (for example pgvector or Qdrant) would need a new ADR superseding the Chroma line above.
