import logging

from app.agent.state.schema import AgentState
from app.agent.tools.security_rules import detect_unsafe_input

logger = logging.getLogger(__name__)

# Generic, user-facing message. Deliberately does not echo which pattern or
# category triggered the block — doing so would help an attacker iteratively
# probe and reverse-engineer the filter. The real reason goes to logs only.
REFUSAL_MESSAGE_UNSAFE = (
    "I can't process this request. Please rephrase your question as a "
    "direct query about the product documentation."
)


def security_agent_node(state: AgentState) -> AgentState:
    print("\n========== SECURITY AGENT ==========")
    print("Question:", state["question"])

     
    """
    First node in the graph. Runs before Document/Retrieval Agents.

    On unsafe input: sets is_safe=False, stores the reason internally for
    logging, and writes final_response directly so this can short-circuit
    straight to the graph's terminal edge without ever reaching FAISS or
    the LLM.

    On safe input: sets is_safe=True and passes the state through
    unchanged otherwise, letting the graph proceed to Document Agent.
    """
    question = state["question"]
    is_unsafe, reason = detect_unsafe_input(question)

    if is_unsafe:
        logger.warning(
            "Security agent blocked request",
            extra={"question": question, "reason": reason},
        )
        return {
            **state,
            "is_safe": False,
            "security_reason": reason,
            "final_response": {
                "answer": REFUSAL_MESSAGE_UNSAFE,
                "confidence_score": None,
                "sources": [],
                "reason": "blocked",
            },
        }

    return {
        **state,
        "is_safe": True,
        "security_reason": None,
    }
