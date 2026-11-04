# 0005. Observability stack

- Status: Accepted
- Date: 2026-11-04

## Context

The service had no application logs and no way to follow a request across log lines or measure it. It must never log keys, file contents, or questions.

## Options

- Logging: `structlog` (contextvars binding, routes stdlib/uvicorn through `ProcessorFormatter`) / `loguru` (non-stdlib handlers, awkward with uvicorn) / stdlib plus `python-json-logger` (no per-request context binding).
- Request ID: `asgi-correlation-id` middleware / hand-written middleware (more code to maintain).
- Metrics: `prometheus-fastapi-instrumentator` / raw `prometheus-client` (more manual code). OpenTelemetry is deferred to deployment.

## Decision

Use `structlog` with JSON output on stdout. Log counts and ids only. Request IDs use `asgi-correlation-id` with its default validator (dashed UUID or 32-hex, which covers nginx and OpenTelemetry IDs); other inbound values are replaced. A structlog processor adds `request_id` to every record, including uvicorn's access line (verified on a running server). Metrics use `prometheus-fastapi-instrumentator` at `GET /metrics` (hidden from OpenAPI, `METRICS_ENABLED` setting, probes and scrapes excluded). Each app gets its own `CollectorRegistry` so several apps can share a process. Per-route latency buckets are widened to 30s for OpenAI-backed routes; the in-progress gauge is not used because the library registers it globally.

## Consequences

- One format for app, stdlib and uvicorn logs; `LOG_JSON=false` gives console output for development.
- `structlog` is added now; `asgi-correlation-id` and `prometheus-fastapi-instrumentator` are added in the steps that use them.
