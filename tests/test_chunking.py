from app.rag.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    """Whitespace-only input produces no chunks."""
    assert chunk_text("   \n\n ", chunk_size_tokens=10, overlap_tokens=0) == []


def test_short_text_is_a_single_chunk() -> None:
    """Text smaller than the chunk size is returned unchanged as one chunk."""
    assert chunk_text("hello world", chunk_size_tokens=800, overlap_tokens=150) == ["hello world"]


def test_paragraphs_are_packed_up_to_chunk_size() -> None:
    """Paragraphs that do not fit together each become their own chunk."""
    paragraphs = [f"paragraph number {index} paragraph number {index}" for index in range(6)]
    # 10 tokens = 40 chars: each 37-char paragraph fills a chunk on its own.
    chunks = chunk_text("\n\n".join(paragraphs), chunk_size_tokens=10, overlap_tokens=0)
    assert chunks == paragraphs


def test_splits_on_markdown_headings() -> None:
    """A new Markdown heading starts a new unit even without a blank line before it."""
    text = "# A\ntext a\n# B\ntext b"
    chunks = chunk_text(text, chunk_size_tokens=3, overlap_tokens=0)
    assert chunks == ["# A\ntext a", "# B\ntext b"]


def test_oversized_unit_falls_back_to_character_window() -> None:
    """A single unit longer than the limit is cut into fixed-size windows."""
    chunks = chunk_text("x" * 100, chunk_size_tokens=10, overlap_tokens=0)
    assert [len(chunk) for chunk in chunks] == [40, 40, 20]


def test_overlap_prefixes_following_chunks_with_previous_tail() -> None:
    """Each chunk after the first starts with the tail of the previous non-overlapped chunk."""
    paragraphs = [f"paragraph number {index} paragraph number {index}" for index in range(3)]
    text = "\n\n".join(paragraphs)
    plain = chunk_text(text, chunk_size_tokens=10, overlap_tokens=0)
    overlapped = chunk_text(text, chunk_size_tokens=10, overlap_tokens=2)  # 8 chars
    assert overlapped[0] == plain[0]
    assert len(overlapped) == len(plain)
    for previous, current, original in zip(plain[:-1], overlapped[1:], plain[1:], strict=True):
        assert current == f"{previous[-8:]}\n\n{original}"
