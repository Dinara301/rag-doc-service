from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.schemas import (
    DocumentListResponse,
    DocumentSummary,
    ErrorResponse,
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    Source,
)
from app.dependencies import OpenAIServicesDep, ServicesDep
from app.rag.ingest import IncomingFile, ingest_documents
from app.rag.qa import answer_question

router = APIRouter()

_ERROR = {"model": ErrorResponse}


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check; always returns `{"status": "ok"}` while the process is up."""
    return HealthResponse(status="ok")


@router.post(
    "/documents",
    response_model=IngestResponse,
    responses={400: _ERROR, 502: _ERROR, 503: _ERROR},
)
def upload_documents(
    services: OpenAIServicesDep,
    files: Annotated[list[UploadFile], File()],
) -> IngestResponse:
    """Upload one or more PDF, Markdown or text files and index them for questions.

    All files are validated before any is stored, so one bad file rejects the request.
    """
    # Read one byte past the limit so oversized files are rejected without loading them fully.
    read_limit = services.settings.max_file_bytes + 1
    incoming = [
        IncomingFile(filename=upload.filename or "unnamed", data=upload.file.read(read_limit))
        for upload in files
    ]
    records = ingest_documents(
        files=incoming,
        settings=services.settings,
        embedder=services.embedder,
        vector_store=services.vector_store,
    )
    return IngestResponse(documents=[DocumentSummary.model_validate(r) for r in records])


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(services: ServicesDep) -> DocumentListResponse:
    """List every ingested document with its chunk count."""
    records = services.vector_store.list_documents()
    return DocumentListResponse(documents=[DocumentSummary.model_validate(r) for r in records])


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: _ERROR},
)
def delete_document(document_id: str, services: ServicesDep) -> None:
    """Delete a document and all its chunks; 404 if the id is unknown."""
    if not services.vector_store.delete_document(document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={502: _ERROR, 503: _ERROR},
)
def query_documents(body: QueryRequest, services: OpenAIServicesDep) -> QueryResponse:
    """Answer a question using only the ingested documents, citing the chunks used."""
    result = answer_question(
        question=body.question,
        top_k=body.top_k,
        embedder=services.embedder,
        generator=services.generator,
        vector_store=services.vector_store,
    )
    return QueryResponse(
        answer=result.answer,
        sources=[
            Source(
                document_id=chunk.document_id,
                filename=chunk.filename,
                snippet=chunk.text,
                score=chunk.score,
            )
            for chunk in result.sources
        ],
    )
