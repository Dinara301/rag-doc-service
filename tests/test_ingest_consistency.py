import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from app.rag.ingest import IncomingFile, ingest_documents
from app.storage.vector_store import ChromaVectorStore, StoredChunk
from tests.conftest import FakeAnswerGenerator, HashEmbedder

FILES = [
    IncomingFile(filename=f"doc-{index}.txt", data=f"Document {index} about widgets.".encode())
    for index in range(3)
]


class StoreFailingOnWrite(ChromaVectorStore):
    """Real Chroma store whose N-th `add_chunks` call fails, optionally after writing."""

    def __init__(self, path: Path, *, fail_on_call: int, write_before_failing: bool) -> None:
        """Open the store and remember when and how to fail."""
        super().__init__(path)
        self.calls = 0
        self.fail_on_call = fail_on_call
        self.write_before_failing = write_before_failing
        self.fail_deletes = False

    def add_chunks(
        self, *, ids: list[str], chunks: list[StoredChunk], embeddings: list[list[float]]
    ) -> None:
        """Write normally until the configured call, which raises (after writing if asked)."""
        self.calls += 1
        if self.calls == self.fail_on_call:
            if self.write_before_failing:
                super().add_chunks(ids=ids, chunks=chunks, embeddings=embeddings)
            raise RuntimeError("simulated store failure")
        super().add_chunks(ids=ids, chunks=chunks, embeddings=embeddings)

    def delete_document(self, document_id: str) -> bool:
        """Delete normally, or fail when `fail_deletes` is set."""
        if self.fail_deletes:
            raise RuntimeError("simulated delete failure")
        return super().delete_document(document_id)


class EmbedderFailingOnCall(HashEmbedder):
    """Hash embedder whose N-th call raises an OpenAI error."""

    def __init__(self, fail_on_call: int) -> None:
        """Remember which call fails."""
        self.calls = 0
        self.fail_on_call = fail_on_call

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed, except on the configured call."""
        self.calls += 1
        if self.calls == self.fail_on_call:
            raise OpenAIError("simulated outage")
        return super().embed_texts(texts)


def _ingest(store: ChromaVectorStore, embedder: HashEmbedder | None = None) -> None:
    """Ingest `FILES` into `store`."""
    ingest_documents(
        files=FILES,
        settings=Settings(),
        embedder=embedder or HashEmbedder(),
        vector_store=store,
    )


@pytest.mark.parametrize("write_before_failing", [False, True], ids=["clean", "partial"])
def test_store_failure_on_second_document_leaves_nothing(
    tmp_path: Path, write_before_failing: bool
) -> None:
    """Documents written earlier in the request, and a partly written one, are removed."""
    store = StoreFailingOnWrite(
        tmp_path / "chroma", fail_on_call=2, write_before_failing=write_before_failing
    )
    try:
        with pytest.raises(RuntimeError, match="simulated store failure"):
            _ingest(store)
        assert store.list_documents() == []
    finally:
        store.close()


def test_embedding_failure_on_a_later_file_stores_nothing(tmp_path: Path) -> None:
    """All files are embedded before any write, so a late OpenAI failure stores nothing."""
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        with pytest.raises(OpenAIError):
            _ingest(store, EmbedderFailingOnCall(fail_on_call=3))
        assert store.list_documents() == []
    finally:
        store.close()


def test_success_path_stores_every_document(tmp_path: Path) -> None:
    """Without failures, all documents are stored with their chunk counts."""
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        records = ingest_documents(
            files=FILES, settings=Settings(), embedder=HashEmbedder(), vector_store=store
        )
        stored = {record.document_id: record.chunk_count for record in store.list_documents()}
        assert stored == {record.document_id: record.chunk_count for record in records}
        assert len(stored) == len(FILES)
    finally:
        store.close()


def test_cleanup_failure_is_logged_and_original_error_raised(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """If cleanup also fails, the write error still surfaces and the leftover is logged."""
    store = StoreFailingOnWrite(tmp_path / "chroma", fail_on_call=2, write_before_failing=False)
    store.fail_deletes = True
    app = create_app(
        Settings(openai_api_key=SecretStr("k"), chroma_path=tmp_path / "unused"),
        vector_store=store,
        embedder=HashEmbedder(),
        generator=FakeAnswerGenerator(),
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        files = [("files", (f.filename, f.data, "text/plain")) for f in FILES]
        response = client.post("/documents", files=files)

    assert response.status_code == 500
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    leftovers = [line for line in lines if line["event"] == "ingest_cleanup_failed"]
    assert len(leftovers) == 2
    assert all(line["error_type"] == "RuntimeError" for line in leftovers)
