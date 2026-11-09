from pathlib import Path

import pytest
from fastapi import FastAPI
from pydantic import SecretStr, ValidationError

from app.config import Settings
from app.main import create_app
from tests.conftest import FakeAnswerGenerator, HashEmbedder
from tests.http import client_for

MAX_FILE = 1_000
MAX_REQUEST = 4_000


class CountingEmbedder(HashEmbedder):
    """Hash embedder that counts calls, to prove rejected uploads never reach OpenAI."""

    def __init__(self) -> None:
        """Start with zero calls."""
        self.calls = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Count the call, then embed as usual."""
        self.calls += 1
        return super().embed_texts(texts)


def _app(tmp_path: Path, embedder: CountingEmbedder) -> FastAPI:
    """App with small per-file and per-request limits."""
    settings = Settings(
        openai_api_key=SecretStr("k"),
        chroma_path=tmp_path / "chroma",
        max_file_bytes=MAX_FILE,
        max_request_bytes=MAX_REQUEST,
    )
    return create_app(settings, embedder=embedder, generator=FakeAnswerGenerator())


def _text_file(name: str, size: int) -> tuple[str, tuple[str, bytes, str]]:
    """A multipart `files` entry with `size` bytes of text."""
    return ("files", (name, b"a" * size, "text/plain"))


def test_oversized_declared_body_returns_413_without_embedding(tmp_path: Path) -> None:
    """A body over the request limit is rejected before parsing; OpenAI is never called."""
    embedder = CountingEmbedder()
    with client_for(_app(tmp_path, embedder)) as client:
        response = client.post("/documents", files=[_text_file("big.txt", MAX_REQUEST * 2)])

    assert response.status_code == 413
    body = response.json()
    assert body["detail"] == f"Request body exceeds the {MAX_REQUEST} byte limit"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert embedder.calls == 0


def test_many_small_files_over_the_request_limit_return_413(tmp_path: Path) -> None:
    """The request limit applies to the whole body, even if each file is under its limit."""
    embedder = CountingEmbedder()
    files = [_text_file(f"part-{index}.txt", MAX_FILE - 100) for index in range(6)]
    with client_for(_app(tmp_path, embedder)) as client:
        response = client.post("/documents", files=files)

    assert response.status_code == 413
    assert embedder.calls == 0


def test_normal_upload_within_limits_still_works(tmp_path: Path) -> None:
    """Uploads under both limits are ingested as before."""
    embedder = CountingEmbedder()
    with client_for(_app(tmp_path, embedder)) as client:
        response = client.post("/documents", files=[_text_file("ok.txt", MAX_FILE - 100)])

    assert response.status_code == 200
    assert embedder.calls == 1


def test_file_over_its_own_limit_is_still_400(tmp_path: Path) -> None:
    """Under the request limit, the existing per-file check still returns 400."""
    embedder = CountingEmbedder()
    with client_for(_app(tmp_path, embedder)) as client:
        response = client.post("/documents", files=[_text_file("big.txt", MAX_FILE + 500)])

    assert response.status_code == 400
    assert embedder.calls == 0


def test_request_limit_smaller_than_file_limit_is_rejected() -> None:
    """Settings refuse a request limit that a single allowed file could not fit in."""
    with pytest.raises(ValidationError, match="max_request_bytes"):
        Settings(max_file_bytes=2_000, max_request_bytes=1_000)
