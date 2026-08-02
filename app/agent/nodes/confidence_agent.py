from app.agent.state.schema import AgentState
from app.utils.config import settings




def confidence_agent_node(state: AgentState) -> AgentState:
    print("\n========== CONFIDENCE AGENT ==========")

    retrieval_result = state.get("retrieval_result")

    score = retrieval_result.top_score if retrieval_result else 0.0
    decision = (
        "proceed"
        if score >= settings.similarity_threshold
        else "refuse"
    )
    print("Confidence:", score)
    print("Threshold:", settings.similarity_threshold)

    return {
        **state,
        "confidence_score": score,
        "decision": decision,
    }

#Dead Code->for computing confidence score, average similarity score of retrieved Top-K chunks.
# def compute_confidence(chunks: list[dict]) -> float:
#     """
#     Confidence = average similarity score of retrieved Top-K chunks.

#     Average (not max) is used deliberately: a single high-similarity chunk
#     surrounded by weak ones is a weaker signal for "the manual actually
#     covers this" than a consistently relevant Top-K. Max is more permissive
#     and would let a single lucky match push borderline answers through.
#     """
#     if not chunks:
#         return 0.0

#     scores = [c["similarity_score"] for c in chunks]
#     return sum(scores) / len(scores)