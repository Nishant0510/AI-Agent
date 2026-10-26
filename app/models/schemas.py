"""
Pydantic request/response models for the FastAPI layer.

These models define the public API contract described in the README:
POST /ask returns {"answer", "confidence_score", "sources": [...]}.
"""

from datetime import datetime
import re
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


class AuthRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)*", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: Literal["user", "admin"]


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class SourceChunk(BaseModel):
    """A single cited source chunk, matching the README response shape."""

    document: str
    page: int
    chunk_id: str
    similarity_score: float


class ChatMessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    confidence_score: Optional[float] = None
    reason: Optional[str] = None
    sources: List[SourceChunk] = Field(default_factory=list)
    created_at: datetime


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    confidence_score: float
    sources: List[SourceChunk] = Field(default_factory=list)
    conversation_id: UUID
    reason: Optional[str] = None


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
