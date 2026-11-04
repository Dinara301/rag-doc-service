import json
import re
import uuid

import pytest

from tests.conftest import AppFactory
from tests.http import client_for

TRACE_ID = uuid.uuid4().hex
FIRST_ID = uuid.uuid4().hex
SECOND_ID = uuid.uuid4().hex
DOCUMENT = ("note.txt", b"Widgets are made by hand.", "text/plain")


def test_response_has_a_generated_request_id(make_app: AppFactory) -> None:
    """Without an inbound header, a fresh ID is generated and returned."""
    with client_for(make_app()) as client:
        first = client.get("/health/live").headers["X-Request-ID"]
        second = client.get("/health/live").headers["X-Request-ID"]

    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert first != second


@pytest.mark.parametrize("inbound", [str(uuid.uuid4()), uuid.uuid4().hex])
def test_inbound_request_id_is_echoed(make_app: AppFactory, inbound: str) -> None:
    """A caller-supplied UUID (dashed or 32-hex, as nginx and OpenTelemetry emit) is kept."""
    with client_for(make_app()) as client:
        response = client.get("/health/live", headers={"X-Request-ID": inbound})

    assert response.headers["X-Request-ID"] == inbound


@pytest.mark.parametrize("bad", ["abc-123", "has space", "x" * 129, 'quote"inject'])
def test_invalid_inbound_request_id_is_replaced(make_app: AppFactory, bad: str) -> None:
    """Values that are not UUIDs are replaced instead of being echoed into logs."""
    with client_for(make_app()) as client:
        response = client.get("/health/live", headers={"X-Request-ID": bad})

    assert response.headers["X-Request-ID"] != bad
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_request_id_appears_in_logs_emitted_during_the_request(
    make_app: AppFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    """Log lines from a request carry its ID; startup lines do not."""
    with client_for(make_app()) as client:
        response = client.post(
            "/documents", files={"files": DOCUMENT}, headers={"X-Request-ID": TRACE_ID}
        )
        assert response.status_code == 200

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    by_event = {line["event"]: line for line in lines}
    assert by_event["documents_ingested"]["request_id"] == TRACE_ID
    assert "request_id" not in by_event["app_started"]


def test_consecutive_requests_keep_separate_ids(
    make_app: AppFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    """Back-to-back requests log under their own IDs, never a previous one."""
    with client_for(make_app()) as client:
        for request_id in (FIRST_ID, SECOND_ID):
            client.post(
                "/documents", files={"files": DOCUMENT}, headers={"X-Request-ID": request_id}
            )

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    ingested = [line["request_id"] for line in lines if line["event"] == "documents_ingested"]
    assert ingested == [FIRST_ID, SECOND_ID]
