import os
from functools import lru_cache
from pathlib import Path

import tiktoken

from app.config import PROJECT_ROOT

# `text-embedding-3-small` (and `-large`) use this encoding, so token counts match what the
# embedding API sees.
ENCODING_NAME: str = "cl100k_base"
DEFAULT_CACHE_DIR: Path = PROJECT_ROOT / ".cache" / "tiktoken"


def configure_cache() -> Path:
    """Point tiktoken at a local cache directory and return it.

    tiktoken downloads its encoding file on first use. Keeping that file in a known directory
    (pre-filled by `scripts/warm_tiktoken.py`) means tests, CI and containers never need network
    access at runtime. An existing `TIKTOKEN_CACHE_DIR` is respected.
    """
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DEFAULT_CACHE_DIR))
    return Path(os.environ["TIKTOKEN_CACHE_DIR"])


@lru_cache(maxsize=1)
def get_encoding() -> tiktoken.Encoding:
    """Return the shared `cl100k_base` encoding, loading it from the local cache."""
    configure_cache()
    return tiktoken.get_encoding(ENCODING_NAME)
