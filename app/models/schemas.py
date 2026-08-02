"""
Pydantic request/response models for the FastAPI layer.

These models define the public API contract described in the README:
POST /ask returns {"answer", "confidence_score", "sources": [...]}.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


class SourceChunk(BaseModel):
    """A single cited source chunk, matching the README response shape."""

    document: str
    page: int
    chunk_id: str
    similarity_score: float


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    confidence_score: float
    sources: List[SourceChunk] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response body for POST /upload."""

    filename: str
    status: str  # e.g. "saved" | "queued_for_ingestion"
    message: str


class SourceDocument(BaseModel):
    """A single ingested document entry for GET /sources."""

    document: str
    num_chunks: Optional[int] = None
    last_ingested_at: Optional[str] = None


class SourcesResponse(BaseModel):
    """Response body for GET /sources."""

    documents: List[SourceDocument] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
    vector_db_ready: bool