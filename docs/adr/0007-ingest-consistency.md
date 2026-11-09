# 0007. Ingest consistency

- Status: Accepted
- Date: 2026-11-09

## Context

Ingest embedded and wrote one file at a time, so an OpenAI or store failure on a later file left earlier files (and possibly part of the failing one) stored, while the client got an error.

## Options

- Embed all, then write; delete this request's documents if a write fails (compensating cleanup).
- No cleanup: simple, but leaves orphan chunks the client does not know about.
- A transactional store (for example pgvector): atomic, but a storage change; noted for Plan 06.

## Decision

Embed every file before writing anything; on a write error, delete every document the request started writing and re-raise. Cleanup failures are logged as `ingest_cleanup_failed` with the document id.

## Consequences

- OpenAI failures store nothing; store failures leave nothing unless the cleanup itself fails, which is logged.
- Peak memory scales with the whole request (all embeddings are held before writing), not one file; `MAX_REQUEST_BYTES` bounds it.
- Not atomic across processes: a crash between write and cleanup can still leave a partial document.
