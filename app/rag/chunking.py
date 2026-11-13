from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from app.rag.tokenizer import get_encoding


def count_tokens(text: str) -> int:
    """Count `cl100k_base` tokens in `text`, treating special-token strings as plain text.

    The library helper `from_tiktoken_encoder` raises on text such as ``<|endoftext|>``, which
    technical documents can legitimately contain, so tokens are counted here instead.
    """
    return len(get_encoding().encode(text, disallowed_special=()))


def chunk_text(text: str, chunk_size_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into Markdown-aware chunks of at most ``chunk_size_tokens`` real tokens.

    Splitting prefers headings, code fences, blank lines, lines and words, in that order, so
    small sections are packed together and large ones are cut at the most natural boundary.
    Consecutive chunks share up to ``overlap_tokens`` tokens; the overlap counts toward the
    size limit, so no chunk is larger than ``chunk_size_tokens``. Text is never rewritten.
    Plain text and PDF extracts go through the same path (they simply have no headings).

    Raises:
        ValueError: ``overlap_tokens`` is larger than ``chunk_size_tokens`` (a library rule;
            `Settings` additionally requires it to be smaller).
    """
    normalized = text.strip()
    if not normalized:
        return []
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.MARKDOWN,
        chunk_size=chunk_size_tokens,
        chunk_overlap=overlap_tokens,
        length_function=count_tokens,
    )
    return [chunk for chunk in splitter.split_text(normalized) if chunk.strip()]
