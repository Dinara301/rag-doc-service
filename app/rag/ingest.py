from dataclasses import dataclass
from uuid import uuid4

import structlog

from app.config import Settings
from app.rag.chunking import chunk_text
from app.rag.llm import Embedder
from app.rag.loaders import extract_text
from app.storage.vector_store import DocumentRecord, StoredChunk, VectorStore

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class IncomingFile:
    """An uploaded file as raw bytes, independent of the web framework."""

    filename: str
    data: bytes


@dataclass(frozen=True)
class _PreparedDocument:
    """A document chunked and embedded in memory, ready to be written."""

    record: DocumentRecord
    ids: list[str]
    chunks: list[StoredChunk]
    embeddings: list[list[float]]


def ingest_documents(
    *,
    files: list[IncomingFile],
    settings: Settings,
    embedder: Embedder,
    vector_store: VectorStore,
) -> list[DocumentRecord]:
    """Validate and embed every file, then write them; a failed request leaves no data behind.

    Order (ADR-0007): extract and validate all files, embed all of them, and only then write.
    If a write fails, every document this request started writing (including a partially
    written one) is deleted before the error is re-raised.

    Raises:
        DocumentRejectedError: any file fails validation (nothing is stored).
        OpenAIError: embedding fails (nothing is stored).
        Exception: a store write fails; already written documents are removed first.
    """
    extracted = [
        (file.filename, extract_text(file.filename, file.data, settings)) for file in files
    ]
    prepared = [
        _prepare(filename=filename, text=text, settings=settings, embedder=embedder)
        for filename, text in extracted
    ]
    _write_all(prepared, vector_store)
    return [document.record for document in prepared]


def _prepare(
    *, filename: str, text: str, settings: Settings, embedder: Embedder
) -> _PreparedDocument:
    """Chunk one document's text and embed the chunks under a new document id (no writes)."""
    pieces = chunk_text(
        text,
        chunk_size_tokens=settings.chunk_size_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    document_id = uuid4().hex
    chunks = [
        StoredChunk(document_id=document_id, filename=filename, text=piece) for piece in pieces
    ]
    return _PreparedDocument(
        record=DocumentRecord(document_id=document_id, filename=filename, chunk_count=len(chunks)),
        ids=[f"{document_id}-{index}" for index in range(len(chunks))],
        chunks=chunks,
        embeddings=embedder.embed_texts([chunk.text for chunk in chunks]),
    )


def _write_all(prepared: list[_PreparedDocument], vector_store: VectorStore) -> None:
    """Write each document; on failure, delete the ones this call touched and re-raise."""
    attempted: list[str] = []
    try:
        for document in prepared:
            attempted.append(document.record.document_id)
            vector_store.add_chunks(
                ids=document.ids, chunks=document.chunks, embeddings=document.embeddings
            )
    except Exception:
        _delete_quietly(attempted, vector_store)
        raise


def _delete_quietly(document_ids: list[str], vector_store: VectorStore) -> None:
    """Best-effort compensating delete; failures are logged so the original error surfaces."""
    for document_id in document_ids:
        try:
            vector_store.delete_document(document_id)
        except Exception as exc:
            log.error(
                "ingest_cleanup_failed", document_id=document_id, error_type=type(exc).__name__
            )
