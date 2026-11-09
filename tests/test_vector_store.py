from pathlib import Path
from typing import Any

import pytest

from app.storage.vector_store import ChromaVectorStore, DocumentRecord, StoredChunk


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


def test_add_chunks_splits_writes_into_batches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """More chunks than the batch size are written in several calls, each chunk once."""
    store = ChromaVectorStore(tmp_path / "chroma", max_batch_size=3)
    batch_sizes: list[int] = []
    original_add = store._collection.add

    def counting_add(**kwargs: Any) -> None:
        batch_sizes.append(len(kwargs["ids"]))
        original_add(**kwargs)

    monkeypatch.setattr(store._collection, "add", counting_add)
    chunks = [StoredChunk(document_id="doc", filename="a.txt", text=f"t{i}") for i in range(8)]
    try:
        store.add_chunks(
            ids=[f"doc-{i}" for i in range(8)],
            chunks=chunks,
            embeddings=[[float(i), 1.0] for i in range(8)],
        )
        assert batch_sizes == [3, 3, 2]
        assert store.list_documents() == [
            DocumentRecord(document_id="doc", filename="a.txt", chunk_count=8)
        ]
    finally:
        store.close()


def test_default_batch_size_comes_from_the_chroma_client(tmp_path: Path) -> None:
    """Without an override, the client's own maximum batch size is used."""
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        assert store._max_batch_size == store._client.get_max_batch_size()
    finally:
        store.close()


def test_add_chunks_with_no_chunks_writes_nothing(tmp_path: Path) -> None:
    """An empty write is a no-op."""
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        store.add_chunks(ids=[], chunks=[], embeddings=[])
        assert store.list_documents() == []
    finally:
        store.close()


def test_more_chunks_than_the_chroma_limit_are_stored(tmp_path: Path) -> None:
    """A write one chunk over the client's real maximum succeeds (a single call would fail)."""
    store = ChromaVectorStore(tmp_path / "chroma")
    count = store._client.get_max_batch_size() + 1
    try:
        store.add_chunks(
            ids=[f"doc-{i}" for i in range(count)],
            chunks=[StoredChunk(document_id="doc", filename="a.txt", text="t")] * count,
            embeddings=[[float(i % 7), 1.0] for i in range(count)],
        )
        assert store.list_documents()[0].chunk_count == count
    finally:
        store.close()
