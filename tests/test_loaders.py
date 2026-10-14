from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.config import Settings
from app.rag.loaders import (
    CorruptDocumentError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    extract_text,
)

SETTINGS = Settings(max_file_bytes=64)


def test_markdown_and_text_are_decoded_and_stripped() -> None:
    """Markdown and text files are decoded as UTF-8, stripped, and matched case-insensitively."""
    assert extract_text("a.md", b"\n# Title\n", SETTINGS) == "# Title"
    assert extract_text("A.TXT", b"  hello ", SETTINGS) == "hello"


def test_unsupported_extension_is_rejected() -> None:
    """Disallowed or missing extensions raise `UnsupportedFileTypeError`."""
    with pytest.raises(UnsupportedFileTypeError):
        extract_text("a.docx", b"x", SETTINGS)
    with pytest.raises(UnsupportedFileTypeError):
        extract_text("no_extension", b"x", SETTINGS)


def test_oversized_file_is_rejected() -> None:
    """Files over `max_file_bytes` raise `FileTooLargeError`."""
    with pytest.raises(FileTooLargeError):
        extract_text("a.txt", b"x" * 65, SETTINGS)


def test_blank_file_is_rejected() -> None:
    """A whitespace-only file raises `EmptyDocumentError`."""
    with pytest.raises(EmptyDocumentError):
        extract_text("a.txt", b"   \n", SETTINGS)


def test_corrupt_pdf_is_rejected() -> None:
    """Bytes that are not a PDF raise `CorruptDocumentError`."""
    with pytest.raises(CorruptDocumentError):
        extract_text("a.pdf", b"not a pdf", SETTINGS)


def test_pdf_without_text_is_rejected() -> None:
    """A valid PDF with no extractable text raises `EmptyDocumentError`."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    with pytest.raises(EmptyDocumentError):
        extract_text("blank.pdf", buffer.getvalue(), Settings(max_file_bytes=10_000))
