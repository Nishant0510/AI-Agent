# app/agent/routers/document_router.py
from app.agent.state.schema import AgentState

# Return values match the edge labels used when wiring this into the graph:
#
#   graph.add_conditional_edges(
#       "document_agent",
#       route_after_document_check,
#       {"no_documents": END, "proceed": "retrieval_agent"},
#   )
#
# Like the security gate, this makes "no documents available" a hard
# code-level short-circuit rather than something the LLM is merely told
# to handle — if documents_available is False, the graph has no edge
# from document_agent to retrieval_agent.


def route_after_document_check(state: AgentState) -> str:
    """Pure routing function — no side effects, no LLM calls."""
    if not state["documents_available"]:
        return "no_documents"
    return "proceed"