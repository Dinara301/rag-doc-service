from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.config import Settings


class DocumentRejectedError(ValueError):
    """The uploaded file cannot be ingested (maps to HTTP 400 at the API edge)."""


class UnsupportedFileTypeError(DocumentRejectedError):
    """The file extension is not in the allowed set."""


class EmptyDocumentError(DocumentRejectedError):
    """The file contains no extractable text."""


class FileTooLargeError(DocumentRejectedError):
    """The file exceeds the configured maximum size."""


class CorruptDocumentError(DocumentRejectedError):
    """The file could not be parsed as the type its extension claims (e.g. a broken PDF)."""


def extract_text(filename: str, data: bytes, settings: Settings) -> str:
    """Validate an uploaded file and return its stripped plain text.

    PDFs are parsed with pypdf; other allowed types are decoded as UTF-8.

    Raises:
        FileTooLargeError: `data` is larger than `settings.max_file_bytes`.
        UnsupportedFileTypeError: the extension is not allowed.
        CorruptDocumentError: a PDF could not be read.
        EmptyDocumentError: no text could be extracted.
    """
    if len(data) > settings.max_file_bytes:
        raise FileTooLargeError(f"{filename} exceeds the {settings.max_file_bytes} byte limit")
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise UnsupportedFileTypeError(f"Unsupported file type: {suffix or '(none)'}")
    text = _pdf_text(filename, data) if suffix == ".pdf" else data.decode("utf-8", errors="replace")
    stripped = text.strip()
    if not stripped:
        raise EmptyDocumentError(f"{filename} contains no extractable text")
    return stripped


def _pdf_text(filename: str, data: bytes) -> str:
    """Extract text from every page of a PDF, translating pypdf errors to `CorruptDocumentError`."""
    try:
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except PyPdfError as exc:
        raise CorruptDocumentError(f"{filename} is not a readable PDF") from exc
