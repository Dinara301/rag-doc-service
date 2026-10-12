from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    chunk_count: int


class IngestResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class Source(BaseModel):
    document_id: str
    filename: str
    snippet: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


class ErrorResponse(BaseModel):
    detail: str
