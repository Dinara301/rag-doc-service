# 0006. OpenAI error mapping and retries

- Status: Accepted
- Date: 2026-11-09

## Context

Every OpenAI failure became 502, so clients could not tell "retry later" from "the service is broken", and the SDK's 10-minute default timeout could hold a worker.

## Options

- Retries: the SDK's built-in `max_retries`/`timeout` / a retry library such as `tenacity` (duplicates what the SDK already does).
- Rate limits: 503 with `Retry-After` / 429 (implies the caller exceeded a limit, but the limit is ours with OpenAI).

## Decision

- Timeout and retries come from settings and are applied to the SDK client.
- `RateLimitError` → 503 + `Retry-After` (upstream value, else 10s); `AuthenticationError`/`PermissionDeniedError` → 503 "misconfigured", logged at error level; `APITimeoutError` → 504; anything else → 502.
- Responses never include upstream text; logs carry the error type and upstream status only.
- FastAPI's 422 body is unchanged.

## Consequences

- Clients can retry 503/504 safely; 502 signals an upstream fault.
- A request can take up to roughly `timeout × (retries + 1)` plus backoff before failing.
