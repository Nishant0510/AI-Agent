# app/models/retrieval.py
from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    document: str
    page: int
    chunk_id: str
    text: str
    similarity_score: float


class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]

    @property
    def top_score(self) -> float:
        return max((c.similarity_score for c in self.chunks), default=0.0)