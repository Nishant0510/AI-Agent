# app/agent/nodes/answer_agent.py

from app.models.retrieval import RetrievedChunk

from app.agent.state.schema import AgentState
from app.llm.provider import generate
from app.prompts.grounded_answer import build_prompt 



# def build_context(chunks: list[RetrievedChunk]) -> str:
#     """Joins retrieved chunk texts into a single context block for the prompt."""
#     return "\n\n".join(
#         f"[Source: {c.document}, page {c.page}]\n{c.text}"
#         for c in chunks
#     )

def answer_agent_node(state: AgentState) -> AgentState:

    print("\n========== ANSWER AGENT ==========")
    print("Generating answer...")

    """
    Only reached when confidence_router says 'proceed'. Builds context
    strictly from retrieved chunks and generates a grounded answer —
    never falls back to the LLM's own knowledge.
    """
    retrieval = state.get("retrieval_result")

    if retrieval is None:
        raise ValueError("No retrieval result available.")

    if not retrieval.chunks:
        raise ValueError("No retrieved chunks available.")

    # context = build_context(retrieval.chunks)

    prompt = build_prompt(
        question=state["question"],
        chunks=retrieval.chunks,
        conversation_history=state.get("conversation_history") or [],
    )


    answer = generate(prompt)

    print("*******Received answer from configured LLM provider*******")
    return {
        **state,
        "answer": answer,
    }
