import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
import tiktoken.registry

from app.rag.tokenizer import ENCODING_NAME, configure_cache, get_encoding


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Make every socket connection fail, and drop in-process encoding caches around the test."""

    def refuse(*args: object, **kwargs: object) -> None:
        raise OSError("network access is blocked in this test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    tiktoken.registry.ENCODINGS.clear()
    get_encoding.cache_clear()
    yield
    tiktoken.registry.ENCODINGS.clear()
    get_encoding.cache_clear()


def test_encoding_loads_offline_from_the_warm_cache(no_network: None) -> None:
    """With the cache warm, the encoding loads and counts tokens with the network blocked."""
    encoding = get_encoding()

    assert encoding.name == ENCODING_NAME
    assert len(encoding.encode("hello world")) == 2


def test_cache_directory_is_what_makes_offline_loading_work(
    no_network: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Control: an empty cache needs a download, which fails here, so the test above is real."""
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(tmp_path))

    with pytest.raises(Exception, match="blocked|Connection|connection"):
        get_encoding()


def test_existing_cache_dir_setting_is_respected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An operator-provided `TIKTOKEN_CACHE_DIR` wins over the project default."""
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(tmp_path))

    assert configure_cache() == tmp_path
