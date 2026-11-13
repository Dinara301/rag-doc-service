import pytest

from app.rag.chunking import chunk_text, count_tokens

SECTION_BODY = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron"


def _sections(count: int) -> str:
    """Markdown with `count` headed sections of roughly 20 tokens each."""
    return "\n\n".join(f"## Section {index}\n\n{SECTION_BODY}" for index in range(count))


def test_empty_text_returns_no_chunks() -> None:
    """Whitespace-only input produces no chunks."""
    assert chunk_text("   \n\n ", chunk_size_tokens=10, overlap_tokens=0) == []


def test_short_text_is_a_single_unchanged_chunk() -> None:
    """Text smaller than the chunk size is returned as one chunk, unchanged."""
    assert chunk_text("hello world", chunk_size_tokens=800, overlap_tokens=150) == ["hello world"]


def test_small_sections_are_packed_into_one_chunk_up_to_the_limit() -> None:
    """Sections that fit together stay together instead of becoming tiny chunks."""
    text = _sections(3)
    assert chunk_text(text, chunk_size_tokens=800, overlap_tokens=150) == [text]


@pytest.mark.parametrize(("size", "overlap"), [(40, 0), (40, 8), (25, 10), (100, 20)])
def test_every_chunk_is_within_the_token_limit(size: int, overlap: int) -> None:
    """Chunk sizes are real `cl100k_base` token counts and never exceed the limit."""
    text = _sections(12) + "\n\n" + "word " * 400
    chunks = chunk_text(text, chunk_size_tokens=size, overlap_tokens=overlap)

    assert len(chunks) > 1
    assert max(count_tokens(chunk) for chunk in chunks) <= size


def test_headings_start_new_chunks_when_sections_do_not_fit_together() -> None:
    """With sections too big to share a chunk, each chunk begins at a heading."""
    chunks = chunk_text(_sections(4), chunk_size_tokens=30, overlap_tokens=0)

    assert len(chunks) == 4
    assert all(chunk.startswith("## Section") for chunk in chunks)
    assert all(chunk.count("## Section") == 1 for chunk in chunks)


def test_overlap_repeats_the_end_of_the_previous_chunk() -> None:
    """With overlap, consecutive chunks share text; without it they share none."""
    lines = [f"Line {index} says something specific about widget {index}." for index in range(40)]
    text = "\n".join(lines)

    plain = chunk_text(text, chunk_size_tokens=60, overlap_tokens=0)
    overlapped = chunk_text(text, chunk_size_tokens=60, overlap_tokens=20)

    assert len(plain) > 1
    for previous, current in zip(plain, plain[1:], strict=False):
        assert not set(previous.splitlines()) & set(current.splitlines())
    for previous, current in zip(overlapped, overlapped[1:], strict=False):
        assert set(previous.splitlines()) & set(current.splitlines())


def test_oversized_single_line_is_split_within_the_limit() -> None:
    """A line with no separators is cut up, every piece within the limit, nothing lost."""
    blob = "x" * 2_000
    chunks = chunk_text(blob, chunk_size_tokens=20, overlap_tokens=0)

    assert len(chunks) > 1
    assert max(count_tokens(chunk) for chunk in chunks) <= 20
    assert "".join(chunks) == blob


def test_text_is_not_rewritten() -> None:
    """Chunks are exact slices of the input: no added trailing spaces, no lost blank lines."""
    text = _sections(6)
    chunks = chunk_text(text, chunk_size_tokens=30, overlap_tokens=0)

    assert all(chunk in text for chunk in chunks)
    assert all("  \n" not in chunk for chunk in chunks)
    assert any("\n\n" in chunk for chunk in chunks)


def test_code_block_that_fits_is_kept_in_one_chunk() -> None:
    """The lines of a code block smaller than the limit are not scattered over chunks.

    The library may move the closing fence to the start of the next chunk; the code lines
    themselves stay together, which is what retrieval needs.
    """
    code_lines = [f"step_{index}()" for index in range(8)]
    fence = "```python\n" + "\n".join(code_lines) + "\n```"
    text = f"# Guide\n\n{'intro words ' * 40}\n\n{fence}\n\nclosing remarks"
    chunks = chunk_text(text, chunk_size_tokens=80, overlap_tokens=0)

    holders = [chunk for chunk in chunks if "step_0()" in chunk]
    assert len(holders) == 1
    assert all(line in holders[0] for line in code_lines)


def test_special_token_text_does_not_raise() -> None:
    """Documents that mention special tokens such as `<|endoftext|>` are chunked as plain text."""
    text = "The model stops at <|endoftext|> markers. " * 30
    chunks = chunk_text(text, chunk_size_tokens=40, overlap_tokens=5)

    assert len(chunks) > 1
    assert any("<|endoftext|>" in chunk for chunk in chunks)


def test_overlap_larger_than_chunk_size_is_rejected_by_the_library() -> None:
    """The splitter refuses an overlap larger than the size; settings reject it earlier."""
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("some text", chunk_size_tokens=10, overlap_tokens=11)
