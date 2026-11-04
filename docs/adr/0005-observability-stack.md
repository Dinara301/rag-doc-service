# 0005. Observability stack

- Status: Accepted
- Date: 2026-11-04

## Context

The service had no application logs and no way to follow a request across log lines or measure it. It must never log keys, file contents, or questions.

## Options

- Logging: `structlog` (contextvars, routes stdlib/uvicorn through `ProcessorFormatter`) / `loguru` (non-stdlib handlers, awkward with uvicorn) / stdlib plus `python-json-logger` (no per-request context).
- Request ID: `asgi-correlation-id` / hand-written middleware (more code to maintain).
- Metrics: `prometheus-fastapi-instrumentator` / raw `prometheus-client` (more manual code). OpenTelemetry is deferred to deployment.

## Decision

- `structlog`, JSON on stdout, counts and ids only.
- `asgi-correlation-id` with its default validator (dashed UUID or 32-hex, which covers nginx and OpenTelemetry IDs; other inbound values are replaced). A processor adds `request_id` to every record, including uvicorn's access line (verified on a running server).
- `prometheus-fastapi-instrumentator` at `GET /metrics`: hidden from OpenAPI, `METRICS_ENABLED` setting, probes excluded, one `CollectorRegistry` per app (with GC, platform and process collectors added), route-latency buckets up to 30s for OpenAI-backed routes. The in-progress gauge is unused (the library registers it globally).

## Consequences

- One log format for app, stdlib and uvicorn; `LOG_JSON=false` gives console output for development.
- The access line is uvicorn's own message (client, request line, status); latency comes from metrics.
- `/metrics` is unauthenticated: keep it private. Counters are per instance, so scrape every replica; several workers in one container need Prometheus multiprocess mode (container plan).
