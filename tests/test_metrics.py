from pathlib import Path

from fastapi import FastAPI

from app.config import Settings
from app.main import create_app
from tests.conftest import AppFactory, FakeAnswerGenerator, HashEmbedder
from tests.http import client_for


def test_metrics_use_route_templates_not_raw_ids(app: FastAPI) -> None:
    """After a request, `/metrics` has the request counter labelled with the route template."""
    with client_for(app) as client:
        assert client.delete("/documents/unique-doc-id-123").status_code == 404
        body = client.get("/metrics").text

    assert "http_requests_total" in body
    assert 'handler="/documents/{document_id}"' in body
    assert 'method="DELETE"' in body
    assert 'status="4xx"' in body
    assert "unique-doc-id-123" not in body
    assert "http_request_duration_seconds" in body
    # Per-route buckets reach past 1s so slow OpenAI-backed routes are visible.
    assert (
        'http_request_duration_seconds_bucket{handler="/documents/{document_id}",le="10.0"' in body
    )


def test_probes_and_scrapes_are_not_counted(app: FastAPI) -> None:
    """Health probes and `/metrics` itself stay out of the request metrics."""
    with client_for(app) as client:
        client.get("/health/live")
        client.get("/health/ready")
        client.get("/metrics")
        body = client.get("/metrics").text

    assert 'handler="/health' not in body
    assert 'handler="/metrics"' not in body


def test_metrics_endpoint_is_hidden_from_the_openapi_schema(app: FastAPI) -> None:
    """`/metrics` is operational, so it is not part of the public API schema."""
    with client_for(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    assert "/metrics" not in paths
    assert "/documents" in paths


def test_runtime_and_process_metrics_are_exposed(app: FastAPI) -> None:
    """The custom registry still reports Python runtime and (on Linux) process metrics."""
    with client_for(app) as client:
        body = client.get("/metrics").text

    assert "python_gc_objects_collected_total" in body
    assert "python_info" in body
    if Path("/proc/self").exists():
        assert "process_resident_memory_bytes" in body
        assert "process_cpu_seconds_total" in body


def test_each_app_has_its_own_metrics(make_app: AppFactory) -> None:
    """Two apps in one process do not share counters or clash on registration."""
    busy, idle = make_app(), make_app()
    with client_for(busy) as busy_client, client_for(idle) as idle_client:
        busy_client.get("/documents")
        busy_body = busy_client.get("/metrics").text
        idle_body = idle_client.get("/metrics").text

    assert 'handler="/documents"' in busy_body
    assert 'handler="/documents"' not in idle_body


def test_metrics_can_be_disabled(tmp_path: Path) -> None:
    """With `metrics_enabled=False` there is no `/metrics` endpoint."""
    settings = Settings(chroma_path=tmp_path / "chroma", metrics_enabled=False)
    app = create_app(settings, embedder=HashEmbedder(), generator=FakeAnswerGenerator())

    with client_for(app) as client:
        assert client.get("/metrics").status_code == 404
