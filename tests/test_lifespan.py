from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.storage.vector_store import (
    ChromaVectorStore,
    DocumentRecord,
    RetrievedChunk,
    StoredChunk,
)
from tests.conftest import FakeAnswerGenerator, HashEmbedder


class RecordingStore:
    """In-memory `VectorStore` that records whether `close` was called."""

    def __init__(self) -> None:
        """Start open and empty."""
        self.closed = False

    def add_chunks(
        self, *, ids: list[str], chunks: list[StoredChunk], embeddings: list[list[float]]
    ) -> None:
        """Ignore writes."""

    def query(self, *, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """Return no results."""
        return []

    def list_documents(self) -> list[DocumentRecord]:
        """Return no documents."""
        return []

    def delete_document(self, document_id: str) -> bool:
        """Report the document as missing."""
        return False

    def close(self) -> None:
        """Record the shutdown."""
        self.closed = True


def test_services_exist_only_while_running_and_store_is_closed(tmp_path: Path) -> None:
    """Startup builds services; shutdown closes the store and drops the services."""
    store = RecordingStore()
    app = create_app(
        Settings(chroma_path=tmp_path / "chroma"),
        vector_store=store,
        embedder=HashEmbedder(),
        generator=FakeAnswerGenerator(),
    )
    assert not hasattr(app.state, "services")

    with TestClient(app) as client:
        assert app.state.services.vector_store is store
        assert store.closed is False
        assert client.get("/documents").status_code == 200

    assert store.closed is True
    assert not hasattr(app.state, "services")


def test_store_is_closed_even_when_the_app_body_fails(tmp_path: Path) -> None:
    """Resources are released when the code running under the lifespan raises."""
    store = RecordingStore()
    app = create_app(
        Settings(chroma_path=tmp_path / "chroma"),
        vector_store=store,
        embedder=HashEmbedder(),
        generator=FakeAnswerGenerator(),
    )

    with pytest.raises(RuntimeError, match="boom"), TestClient(app):
        raise RuntimeError("boom")

    assert store.closed is True


def test_default_chroma_store_starts_and_restarts_on_same_path(tmp_path: Path) -> None:
    """The default Chroma store is built at startup and can be reopened after shutdown."""
    settings = Settings(chroma_path=tmp_path / "chroma")

    for _ in range(2):
        app = create_app(settings, embedder=HashEmbedder(), generator=FakeAnswerGenerator())
        with TestClient(app) as client:
            assert isinstance(app.state.services.vector_store, ChromaVectorStore)
            assert client.get("/documents").json() == {"documents": []}
