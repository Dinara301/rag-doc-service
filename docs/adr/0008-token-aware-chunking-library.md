# 0008. Token-aware chunking with a library

- Status: Accepted
- Date: 2026-11-13

## Context

`app/rag/chunking.py` guesses tokens as 4 characters, so chunk sizes drift from what the embedding model sees, and the hand-written splitter must handle Markdown, code and long lines itself.

## Options

- `langchain-text-splitters` + `tiktoken`: Markdown-aware and token-exact splitters, widely used; pulls in `langchain-core`.
- `semchunk`: small, but no Markdown structure awareness.
- `chonkie`: newer, smaller community.
- Keep hand-written: guessed token counts and more code to maintain.

## Decision

Adopt `langchain-text-splitters` (splitter package only, no chains or retrievers) and `tiktoken` with `cl100k_base`, the encoding of `text-embedding-3-small`. `tiktoken` downloads that file on first use, so `TIKTOKEN_CACHE_DIR` points at `.cache/tiktoken`, filled by `scripts/warm_tiktoken.py`; tests refuse to run on an empty cache instead of downloading.

## Consequences

- Chunk limits become exact token counts; no network is needed at test or run time once the cache is warm.
- Setup gains one step (the warm script); container builds must run it (Plan 08).
- `langchain-core` and its dependencies are installed; the RAG pipeline itself stays explicit.
- Chunk boundaries will change in the next step, so existing documents should be re-ingested.
