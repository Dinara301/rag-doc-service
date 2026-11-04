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

Use `structlog` with JSON output on stdout. Log counts and ids only. Request IDs and metrics decisions are appended to this ADR as steps 3.2 and 3.3 land.

## Consequences

- One format for app, stdlib and uvicorn logs; `LOG_JSON=false` gives console output for development.
- `structlog` is added now; `asgi-correlation-id` and `prometheus-fastapi-instrumentator` are added in the steps that use them.
