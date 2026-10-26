# app/agent/state/schema.py
from app.models.retrieval import RetrievalResult  # wherever these live
from app.models.citation import SourceCitation
from typing import TypedDict
from typing import Optional


class FinalResponse(TypedDict):
    answer: Optional[str]
    confidence_score: Optional[float]
    sources: list[SourceCitation]
    reason: Optional[str] 



class AgentState(TypedDict):
    question: str
    # Recent user/assistant turns for resolving follow-up questions. The
    # checkpointer scopes this history to one conversation thread.
    conversation_history: list[dict[str, str]]
    is_safe: bool
    documents_available: bool
    retrieval_result: RetrievalResult | None
    confidence_score: float | None
    decision: str | None           # "proceed" | "refuse"
    rag_decision: str | None        # "use_rag" | "direct_llm"
    answer: str | None
    sources: list[SourceCitation] | None
    is_grounded: bool | None
    refusal_reason: str | None      # new
    final_response: FinalResponse | None


# class RetrievedChunk(TypedDict):
#     document: str
#     page: int
#     chunk_id: str
#     similarity_score: float
#     text: str

# class RetrievalResult(TypedDict):
#     chunks: list[RetrievedChunk]
#     top_score: float 

        


