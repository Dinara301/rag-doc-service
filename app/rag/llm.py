from typing import Protocol

from openai import OpenAI

from app.storage.vector_store import RetrievedChunk

SYSTEM_PROMPT: str = (
    "You answer questions using only the provided documentation snippets. "
    "If the snippets are insufficient, say you do not have enough information. "
    "Do not invent APIs, versions, or file names."
)
EMBEDDING_BATCH_SIZE: int = 100


class Embedder(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class AnswerGenerator(Protocol):
    def generate_answer(self, question: str, snippets: list[RetrievedChunk]) -> str: ...


class OpenAIEmbedder:
    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + EMBEDDING_BATCH_SIZE]
            response = self._client.embeddings.create(model=self._model, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(list(item.embedding) for item in ordered)
        return vectors


class OpenAIAnswerGenerator:
    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def generate_answer(self, question: str, snippets: list[RetrievedChunk]) -> str:
        context = "\n\n".join(
            f"[{index}] {chunk.filename}: {chunk.text}"
            for index, chunk in enumerate(snippets, start=1)
        )
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Snippets:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0,
        )
        content = completion.choices[0].message.content
        return content.strip() if content else ""
