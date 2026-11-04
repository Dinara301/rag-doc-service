from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator

# Per-route latency buckets (seconds). The library default stops at 1s, which cannot show the
# multi-second OpenAI calls behind /documents and /query.
_ROUTE_LATENCY_BUCKETS: tuple[float, ...] = (0.1, 0.5, 1, 2.5, 5, 10, 30)

# Handlers (regex on the path) kept out of request metrics so probes and scrapes do not
# dominate the numbers.
_EXCLUDED_HANDLERS: list[str] = ["/metrics", "/health.*"]


def setup_metrics(app: FastAPI) -> None:
    """Record HTTP request metrics for `app` and expose them at `GET /metrics`.

    Each app gets its own `CollectorRegistry`, so several apps can live in one process (tests)
    without duplicate-metric errors. The `handler` label is the route template
    (`/documents/{document_id}`), never the raw URL, which keeps label cardinality bounded.
    The endpoint is hidden from the OpenAPI schema and is unauthenticated: keep it on a
    private network.
    """
    instrumentator = Instrumentator(
        registry=CollectorRegistry(),
        excluded_handlers=_EXCLUDED_HANDLERS,
    )
    instrumentator.instrument(app, latency_lowr_buckets=_ROUTE_LATENCY_BUCKETS).expose(
        app, include_in_schema=False
    )
