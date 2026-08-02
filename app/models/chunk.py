from pydantic import BaseModel, Field
from typing import Optional


class ChunkMetadata(BaseModel):
    """Metadata attached to every chunk for citation purposes."""
    document_name: str
    page_number: int
    chunk_id: str
    chunk_index: int  # position within the document, useful for debugging/ordering


class DocumentChunk(BaseModel):
    """A single chunk of text plus its metadata."""
    text: str
    metadata: ChunkMetadata


class SearchResult(BaseModel):
    """A chunk returned from FAISS search, with its similarity score."""
    chunk: DocumentChunk
    similarity_score: float