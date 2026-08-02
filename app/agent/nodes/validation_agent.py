from app.agent.state.schema import AgentState
from app.models.citation import SourceCitation

REFUSAL_MESSAGE_UNGROUNDED = (
    "I wasn't able to verify this answer against the source documentation, "
    "so I can't provide it with confidence."
)


def has_citations(sources: list[SourceCitation]) -> bool:
    return len(sources) > 0


def validation_agent_node(state: AgentState) -> AgentState:
    print("\n========== VALIDATION AGENT ==========")
    grounded = (
    bool(state["answer"])
    and bool(state["sources"])
    and state["confidence_score"] > 0
)

    if not grounded:
        print("Validation Failed: Answer is not grounded in source documentation.")
        return {
            **state,
            "is_grounded": False,
            "final_response": {
                "answer": REFUSAL_MESSAGE_UNGROUNDED,
                "confidence_score": state["confidence_score"],
                "sources": [],
            },
        }
    print("Validation Passed")
    return {
        **state,
        "is_grounded": True,
        "final_response": {
            "answer": state["answer"],
            "confidence_score": state["confidence_score"],
            "sources": state["sources"],
        },
    }