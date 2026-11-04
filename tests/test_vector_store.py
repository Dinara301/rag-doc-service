from pathlib import Path

import pytest

from app.storage.vector_store import ChromaVectorStore


def test_ping_is_true_for_a_healthy_store(tmp_path: Path) -> None:
    """A freshly opened Chroma store answers its heartbeat."""
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        assert store.ping() is True
    finally:
        store.close()


def test_ping_is_false_when_the_client_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Any client error is reported as unreachable instead of propagating."""
    store = ChromaVectorStore(tmp_path / "chroma")

    def broken_heartbeat() -> int:
        raise ConnectionError("chroma is down")

    monkeypatch.setattr(store._client, "heartbeat", broken_heartbeat)
    try:
        assert store.ping() is False
    finally:
        store.close()
