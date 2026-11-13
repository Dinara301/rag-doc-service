"""Download the tiktoken encoding into the local cache so later runs need no network.

Run once per checkout (and at container build time)::

    uv run python scripts/warm_tiktoken.py
"""

from app.rag.tokenizer import ENCODING_NAME, configure_cache, get_encoding


def main() -> None:
    """Load the encoding (downloading it if the cache is empty) and report the cache location."""
    cache_dir = configure_cache()
    encoding = get_encoding()
    files = sorted(path.name for path in cache_dir.iterdir()) if cache_dir.exists() else []
    print(f"{ENCODING_NAME}: {encoding.n_vocab} tokens; cache {cache_dir} ({len(files)} file(s))")


if __name__ == "__main__":
    main()
