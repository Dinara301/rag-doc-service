import re

_UNIT_SPLIT = re.compile(r"(?=^#{1,6} )|\n{2,}", flags=re.MULTILINE)
_CHARS_PER_TOKEN: int = 4
_UNIT_SEPARATOR: str = "\n\n"


def chunk_text(text: str, chunk_size_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into chunks of roughly ``chunk_size_tokens``.

    Units are Markdown sections / paragraphs. Oversized units fall back to a
    fixed character window. Each chunk after the first is prefixed with the
    last ``overlap_tokens`` of the previous chunk, so it may exceed the
    nominal size by up to the overlap.
    """
    normalized = text.strip()
    if not normalized:
        return []

    chunk_size_chars = max(chunk_size_tokens * _CHARS_PER_TOKEN, 1)
    overlap_chars = max(overlap_tokens * _CHARS_PER_TOKEN, 0)
    packed = _pack_units(_split_units(normalized), chunk_size_chars)
    if overlap_chars == 0 or len(packed) <= 1:
        return packed
    return _apply_overlap(packed, overlap_chars)


def _split_units(text: str) -> list[str]:
    units = [part.strip() for part in _UNIT_SPLIT.split(text) if part.strip()]
    return units or [text]


def _pack_units(units: list[str], chunk_size_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    separator_len = len(_UNIT_SEPARATOR)

    def flush() -> None:
        nonlocal current, current_len
        if current:
            chunks.append(_UNIT_SEPARATOR.join(current))
            current = []
            current_len = 0

    for unit in units:
        if len(unit) > chunk_size_chars:
            flush()
            chunks.extend(_window(unit, chunk_size_chars))
            continue
        added_len = len(unit) + (separator_len if current else 0)
        if current and current_len + added_len > chunk_size_chars:
            flush()
            added_len = len(unit)
        current.append(unit)
        current_len += added_len
    flush()
    return chunks


def _window(text: str, chunk_size_chars: int) -> list[str]:
    windows = (
        text[start : start + chunk_size_chars].strip()
        for start in range(0, len(text), chunk_size_chars)
    )
    return [window for window in windows if window]


def _apply_overlap(chunks: list[str], overlap_chars: int) -> list[str]:
    overlapped = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:], strict=False):
        overlapped.append(f"{previous[-overlap_chars:]}{_UNIT_SEPARATOR}{current}".strip())
    return overlapped
