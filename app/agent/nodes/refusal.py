from app.agent.state.schema import AgentState

REASON_MESSAGES = {
    "blocked": (
        "This question couldn't be processed due to a security check. "
        "Please rephrase your question."
    ),
    "no_documents": (
        "No product manuals are currently indexed. Please upload the "
        "relevant Philips product manual and try again."
    ),
    "low_confidence": (
        "I don't have enough confidence in the retrieved documentation to "
        "answer this accurately. Please rephrase your question or verify "
        "the relevant product manual has been uploaded."
    ),
}


def _infer_reason(state: AgentState) -> str:
    if not state.get("is_safe", True):
        return "blocked"
    if not state.get("documents_available", True):
        return "no_documents"
    return "low_confidence"

def refusal_node(state: AgentState) -> AgentState:
    reason = _infer_reason(state)
    message = REASON_MESSAGES[reason]

    print(f"\n========== REFUSAL NODE ==========")
    print(f"reason={reason}")
    print(f"confidence_score={state.get('confidence_score')}")
    print(f"message={message}")

    return {
        **state,
        "answer": None,
        "sources": [],
        "is_grounded": False,
        "refusal_reason": reason,          # new — see schema change below
        "final_response": {
            "answer": message,
            "confidence_score": state.get("confidence_score"),
            "sources": [],
            "reason": reason,
        },
    }
# def refusal_node(state: AgentState) -> AgentState:
#     print("\n========== REFUSAL NODE ==========")
#     reason = _infer_reason(state)
   
#     print("Message:", state["answer"])
#     return {
#         **state,
#         "answer": None,
#         "sources": [],
#         "is_grounded": False,
#         "final_response": {
#             "answer": REASON_MESSAGES[reason],
#             "confidence_score": state.get("confidence_score"),
#             "sources": [],
#         },
#     }
