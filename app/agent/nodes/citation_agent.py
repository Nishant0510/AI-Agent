
#app/agent/nodes/citation_agent.py
from app.agent.state.schema import AgentState
from app.models.citation import SourceCitation

def format_sources(retrieval_result) -> list[SourceCitation]:
    return [
        {
            "document": chunk.document,
            "page": chunk.page,
            "chunk_id": chunk.chunk_id,
            "similarity_score": chunk.similarity_score,
        }
        for chunk in retrieval_result.chunks
    ]


def citation_agent_node(state: AgentState) -> AgentState:
    print("\n========== CITATION AGENT ==========")
    retrieval = state.get("retrieval_result")

    if retrieval is None:
        return {
            **state,
            "sources": [],
        }
    print("Formatting sources for citation...")
    return {
        **state,
        "sources": format_sources(retrieval),
    }