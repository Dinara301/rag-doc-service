from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.config import Settings


class DocumentRejectedError(ValueError):
    """The uploaded file cannot be ingested (maps to HTTP 400 at the API edge)."""


class UnsupportedFileTypeError(DocumentRejectedError):
    pass


class EmptyDocumentError(DocumentRejectedError):
    pass


class FileTooLargeError(DocumentRejectedError):
    pass


class CorruptDocumentError(DocumentRejectedError):
    pass


def extract_text(filename: str, data: bytes, settings: Settings) -> str:
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
    try:
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except PyPdfError as exc:
        raise CorruptDocumentError(f"{filename} is not a readable PDF") from exc
