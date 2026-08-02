# app/agent/graph/build_graph.py

from langgraph.graph import StateGraph, END

from app.agent.state.schema import AgentState
from app.agent.nodes.security_agent import security_agent_node
from app.agent.nodes.document_agent import document_agent_node
from app.agent.nodes.retrieval_agent import retrieval_agent_node
from app.agent.nodes.confidence_agent import confidence_agent_node
from app.agent.nodes.answer_agent import answer_agent_node
from app.agent.nodes.citation_agent import citation_agent_node
from app.agent.nodes.validation_agent import validation_agent_node
from app.agent.nodes.refusal import refusal_node
from app.agent.routers.security_router import route_after_security
from app.agent.routers.document_router import route_after_document_check
from app.agent.routers.confidence_router import route_on_confidence


def build_graph():
    print("Building agent graph...")
    graph = StateGraph(AgentState)

    graph.add_node("security_agent", security_agent_node)
    graph.add_node("document_agent", document_agent_node)
    graph.add_node("retrieval_agent", retrieval_agent_node)
    graph.add_node("confidence_agent", confidence_agent_node)
    graph.add_node("answer_agent", answer_agent_node)
    graph.add_node("citation_agent", citation_agent_node)
    graph.add_node("validation_agent", validation_agent_node)
    graph.add_node("refusal", refusal_node)

    graph.set_entry_point("security_agent")

    # Security gate — hard code-level short-circuit, no edge to
    # document_agent exists when blocked.
    graph.add_conditional_edges(
        "security_agent",
        route_after_security,
        {"blocked": "refusal", "proceed": "document_agent"},
    )

    # Document availability gate
    graph.add_conditional_edges(
        "document_agent",
        route_after_document_check,
        {"no_documents": "refusal", "proceed": "retrieval_agent"},
    )

    graph.add_edge("retrieval_agent", "confidence_agent")

    # Confidence gate — LLM generation node has no incoming edge when
    # confidence is below threshold.
    graph.add_conditional_edges(
        "confidence_agent",
        route_on_confidence,
        {"refuse": "refusal", "proceed": "answer_agent"},
    )

    graph.add_edge("answer_agent", "citation_agent")
    graph.add_edge("citation_agent", "validation_agent")
    graph.add_edge("validation_agent", END)
    graph.add_edge("refusal", END)
    print("Graph built successfully.")
    return graph.compile()

compiled_graph = build_graph()    
