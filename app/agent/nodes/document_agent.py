# app/agent/nodes/document_agent.py

import logging

from app.agent.state.schema import AgentState
from app.vectorstore.store import vector_store_exists  # adjust to your actual accessor

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE_NO_DOCS = (
    "No product documentation is currently available to search. Please "
    "upload the relevant manual first."
)


def document_agent_node(state: AgentState) -> AgentState:
    
    print("\n========== DOCUMENT AGENT ==========")
    print("Searchinng for product documentation in the FAISS vector store...")

    """
    Confirms the FAISS index exists and is non-empty before we bother
    embedding the query. Cheap check, avoids wasted retrieval calls.
    """
    available = vector_store_exists()

    if not available:
        logger.info("Document agent found no available vector store")
        return {
            **state,
            "documents_available": False,
            "final_response": {
                "answer": REFUSAL_MESSAGE_NO_DOCS,
                "confidence_score": None,
                "sources": [],
            },
        }
    print("Product documentation found in the FAISS vector store.")
    return {
        **state,
        "documents_available": True,
    }