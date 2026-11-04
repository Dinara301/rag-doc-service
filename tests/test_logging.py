import json
import logging

import pytest
import structlog

from app.logging_config import configure_logging
from tests.conftest import AppFactory
from tests.http import client_for

API_KEY_CANARY = "sk-canary-1234"
DOCUMENT_TEXT = "CONFIDENTIAL-DOCUMENT-TEXT: the widget launch code is 4242."
QUESTION = "CONFIDENTIAL-QUESTION: what is the launch code?"


def _json_lines(output: str) -> list[dict[str, object]]:
    """Parse every non-empty output line as a JSON object."""
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_log_lines_are_json_with_level_event_and_timestamp(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Structlog events and stdlib/uvicorn records share one JSON format."""
    configure_logging("INFO", json_logs=True)

    structlog.get_logger("demo").info("hello", answer=42)
    logging.getLogger("uvicorn.error").info("from uvicorn")

    first, second = _json_lines(capsys.readouterr().out)
    assert first["event"] == "hello"
    assert first["answer"] == 42
    assert first["level"] == "info"
    assert first["logger"] == "demo"
    assert str(first["timestamp"]).endswith("Z")
    assert second["event"] == "from uvicorn"
    assert second["logger"] == "uvicorn.error"


def test_log_level_filters_lower_levels(capsys: pytest.CaptureFixture[str]) -> None:
    """Events below the configured level are dropped."""
    configure_logging("WARNING", json_logs=True)

    log = structlog.get_logger("demo")
    log.info("quiet")
    log.warning("loud")

    assert [line["event"] for line in _json_lines(capsys.readouterr().out)] == ["loud"]


def test_console_mode_is_not_json(capsys: pytest.CaptureFixture[str]) -> None:
    """With `json_logs=False` output is human-readable, not JSON."""
    configure_logging("INFO", json_logs=False)

    structlog.get_logger("demo").info("hello")

    out = capsys.readouterr().out
    assert "hello" in out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)


def test_repeated_configuration_does_not_duplicate_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Calling `configure_logging` again replaces its handler instead of adding another."""
    configure_logging("INFO", json_logs=True)
    configure_logging("INFO", json_logs=True)

    structlog.get_logger("demo").info("once")

    assert len(_json_lines(capsys.readouterr().out)) == 1


def test_request_logs_never_contain_key_document_text_or_question(
    make_app: AppFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ingest and query log counts and ids only, never secrets or user content."""
    app = make_app(api_key=API_KEY_CANARY)
    with client_for(app) as client:
        upload = client.post(
            "/documents", files={"files": ("secret.txt", DOCUMENT_TEXT.encode(), "text/plain")}
        )
        assert upload.status_code == 200
        query = client.post("/query", json={"question": QUESTION, "top_k": 3})
        assert query.status_code == 200

    output = capsys.readouterr().out
    events = [line["event"] for line in _json_lines(output)]
    assert {"app_started", "documents_ingested", "query_answered"} <= set(events)
    for sensitive in (API_KEY_CANARY, "CONFIDENTIAL", "launch code", "4242", "secret.txt"):
        assert sensitive not in output
