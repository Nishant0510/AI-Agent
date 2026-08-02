from pydantic import BaseModel
from typing import TypedDict
class SourceCitation(TypedDict):
    document: str
    page: int
    chunk_id: str
    similarity_score: float  