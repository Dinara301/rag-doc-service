from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass(frozen=True)
class StoredChunk:
    document_id: str
    filename: str
    text: str


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    filename: str
    text: str
    score: float


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    filename: str
    chunk_count: int


_ChromaEmbeddings = list[Sequence[float] | Sequence[int]]


class VectorStore(Protocol):
    def add_chunks(
        self,
        *,
        ids: list[str],
        chunks: list[StoredChunk],
        embeddings: list[list[float]],
    ) -> None: ...

    def query(self, *, embedding: list[float], top_k: int) -> list[RetrievedChunk]: ...

    def list_documents(self) -> list[DocumentRecord]: ...

    def delete_document(self, document_id: str) -> bool: ...


class ChromaVectorStore:
    def __init__(self, persist_path: Path, collection_name: str = "documents") -> None:
        persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        *,
        ids: list[str],
        chunks: list[StoredChunk],
        embeddings: list[list[float]],
    ) -> None:
        if not ids:
            return
        vectors: _ChromaEmbeddings = [*embeddings]
        self._collection.add(
            ids=ids,
            documents=[chunk.text for chunk in chunks],
            embeddings=vectors,
            metadatas=[
                {"document_id": chunk.document_id, "filename": chunk.filename} for chunk in chunks
            ],
        )

    def query(self, *, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        total = self._collection.count()
        if total == 0:
            return []
        query_vectors: _ChromaEmbeddings = [embedding]
        result = self._collection.query(
            query_embeddings=query_vectors,
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=True):
            if text is None or metadata is None:
                continue
            retrieved.append(
                RetrievedChunk(
                    document_id=str(metadata["document_id"]),
                    filename=str(metadata["filename"]),
                    text=text,
                    score=max(0.0, min(1.0, 1.0 - float(distance))),
                )
            )
        return retrieved

    def list_documents(self) -> list[DocumentRecord]:
        payload = self._collection.get(include=["metadatas"])
        chunk_counts: Counter[tuple[str, str]] = Counter()
        for metadata in payload.get("metadatas") or []:
            if metadata is not None:
                chunk_counts[(str(metadata["document_id"]), str(metadata["filename"]))] += 1
        return [
            DocumentRecord(document_id=document_id, filename=filename, chunk_count=count)
            for (document_id, filename), count in chunk_counts.items()
        ]

    def delete_document(self, document_id: str) -> bool:
        existing = self._collection.get(where={"document_id": document_id})
        ids = existing.get("ids") or []
        if not ids:
            return False
        self._collection.delete(ids=ids)
        return True
