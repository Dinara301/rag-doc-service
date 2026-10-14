import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi import FastAPI
from openai import OpenAIError

from app.config import Settings
from app.main import create_app
from app.rag.llm import Embedder
from app.storage.vector_store import RetrievedChunk

AppFactory = Callable[..., FastAPI]


class HashEmbedder:
    """Deterministic bag-of-words embedding; replaces the OpenAI embeddings API."""

    dim: int = 32

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed each text as a normalized word-hash histogram."""
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        """Hash each word into one of `dim` buckets and L2-normalize the counts."""
        vector = [0.0] * self.dim
        for word in text.lower().split():
            bucket = int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big")
            vector[bucket % self.dim] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]


class FailingEmbedder:
    """Embedder that always raises `OpenAIError`, to exercise the 502 path."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Raise `OpenAIError` instead of embedding."""
        raise OpenAIError("simulated OpenAI outage")


class FakeAnswerGenerator:
    """Answer generator that echoes the question and top snippet; replaces the chat API."""

    def generate_answer(self, question: str, snippets: list[RetrievedChunk]) -> str:
        """Return a deterministic answer built from the question and the first snippet."""
        first = snippets[0]
        return f"Answer for '{question}' from {first.filename}: {first.text[:120]}"


@pytest.fixture
def make_app(tmp_path: Path) -> AppFactory:
    """Factory fixture building an app with fake OpenAI services and a temporary Chroma store."""

    def _make(*, api_key: str = "test-key", embedder: Embedder | None = None) -> FastAPI:
        """Create an app; `api_key` and `embedder` can be overridden per test."""
        settings = Settings(openai_api_key=api_key, chroma_path=tmp_path / "chroma")
        return create_app(
            settings,
            embedder=embedder or HashEmbedder(),
            generator=FakeAnswerGenerator(),
        )

    return _make


@pytest.fixture
def app(make_app: AppFactory) -> FastAPI:
    """Default app: API key set, hash embedder, fake generator."""
    return make_app()
