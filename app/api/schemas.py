from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: str


class DocumentSummary(BaseModel):
    """An ingested document: its id, original filename and number of stored chunks."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    chunk_count: int


class IngestResponse(BaseModel):
    """Documents created by one upload request, in upload order."""

    documents: list[DocumentSummary]


class DocumentListResponse(BaseModel):
    """All documents currently stored."""

    documents: list[DocumentSummary]


class QueryRequest(BaseModel):
    """A question to answer from the ingested documents."""

    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class Source(BaseModel):
    """A retrieved chunk that supports the answer, with its similarity score in [0, 1]."""

    document_id: str
    filename: str
    snippet: str
    score: float


class QueryResponse(BaseModel):
    """The generated answer and the sources it is grounded in."""

    answer: str
    sources: list[Source]


class ErrorResponse(BaseModel):
    """Error body returned for 4xx/5xx responses."""

    detail: str
