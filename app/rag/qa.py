from dataclasses import dataclass

from app.rag.llm import AnswerGenerator, Embedder
from app.storage.vector_store import RetrievedChunk, VectorStore

EMPTY_CORPUS_ANSWER: str = "No documents are available yet. Ingest files before asking questions."
NO_HITS_ANSWER: str = "I do not have enough information in the ingested documents to answer that."


@dataclass(frozen=True)
class QueryResult:
    """An answer plus the retrieved chunks it is grounded in."""

    answer: str
    sources: list[RetrievedChunk]


def answer_question(
    *,
    question: str,
    top_k: int,
    embedder: Embedder,
    generator: AnswerGenerator,
    vector_store: VectorStore,
) -> QueryResult:
    """Embed the question, retrieve the `top_k` nearest chunks and generate a grounded answer.

    When nothing is retrieved, return a fixed message (distinguishing an empty corpus from
    no relevant hits) with no sources, without calling the generator.
    """
    query_embedding = embedder.embed_texts([question])[0]
    retrieved = vector_store.query(embedding=query_embedding, top_k=top_k)
    if not retrieved:
        has_documents = bool(vector_store.list_documents())
        return QueryResult(
            answer=NO_HITS_ANSWER if has_documents else EMPTY_CORPUS_ANSWER,
            sources=[],
        )
    return QueryResult(
        answer=generator.generate_answer(question, retrieved),
        sources=retrieved,
    )
