from dataclasses import dataclass
from uuid import uuid4

from app.config import Settings
from app.rag.chunking import chunk_text
from app.rag.llm import Embedder
from app.rag.loaders import extract_text
from app.storage.vector_store import DocumentRecord, StoredChunk, VectorStore


@dataclass(frozen=True)
class IncomingFile:
    filename: str
    data: bytes


def ingest_documents(
    *,
    files: list[IncomingFile],
    settings: Settings,
    embedder: Embedder,
    vector_store: VectorStore,
) -> list[DocumentRecord]:
    """Validate every file first, then embed and store, so bad input stores nothing."""
    extracted = [
        (file.filename, extract_text(file.filename, file.data, settings)) for file in files
    ]
    return [
        _ingest_text(
            filename=filename,
            text=text,
            settings=settings,
            embedder=embedder,
            vector_store=vector_store,
        )
        for filename, text in extracted
    ]


def _ingest_text(
    *,
    filename: str,
    text: str,
    settings: Settings,
    embedder: Embedder,
    vector_store: VectorStore,
) -> DocumentRecord:
    pieces = chunk_text(
        text,
        chunk_size_tokens=settings.chunk_size_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    document_id = uuid4().hex
    chunks = [
        StoredChunk(document_id=document_id, filename=filename, text=piece) for piece in pieces
    ]
    embeddings = embedder.embed_texts([chunk.text for chunk in chunks])
    ids = [f"{document_id}-{index}" for index in range(len(chunks))]
    vector_store.add_chunks(ids=ids, chunks=chunks, embeddings=embeddings)
    return DocumentRecord(document_id=document_id, filename=filename, chunk_count=len(chunks))
