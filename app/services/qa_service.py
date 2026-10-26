"""
Thin service layer that invokes the compiled LangGraph agent pipeline
for question answering.

This module is intentionally the ONLY place that adapts between the
FastAPI request/response shape and the LangGraph state schema. If the
real GraphState differs from the minimal contract assumed here
(a dict with "question", "answer", "confidence_score", "sources"),
update the mapping in `_to_ask_response` only.
"""

from threading import Lock
from typing import Any, Dict
from app.agent.graph.callback import PipelineLoggingCallback
from app.services.logging_service import RequestLogContext

from app.models.schemas import AskResponse, SourceChunk

_MAX_MEMORY_MESSAGES = 12  # six recent user/assistant turns
_conversation_locks: dict[str, Lock] = {}
_conversation_locks_guard = Lock()


def _lock_for_conversation(conversation_id: str) -> Lock:
    # Serialize turns in a conversation so concurrent requests cannot lose
    # checkpoint updates.
    with _conversation_locks_guard:
        return _conversation_locks.setdefault(conversation_id, Lock())


class GraphNotReadyError(RuntimeError):
    """Raised when the compiled graph has not been initialized."""




def _to_ask_response(
    graph_output: Dict[str, Any], conversation_id: str
) -> AskResponse:
    """
    Map raw LangGraph output state to the public AskResponse shape.

    The graph's authoritative output lives under state["final_response"],
    populated by either validation_agent_node (success) or refusal_node
    (refusal). Top-level state["answer"]/["sources"] are intermediate
    working fields, not the response contract — do not read them here.
    """
    final = graph_output.get("final_response") or {}

    raw_sources = final.get("sources", []) or []
    sources = [
        SourceChunk(
            document=s["document"],
            page=s["page"],
            chunk_id=s["chunk_id"],
            similarity_score=s["similarity_score"],
        )
        for s in raw_sources
    ]
    return AskResponse(
        answer=final.get("answer") or "",
        confidence_score=final.get("confidence_score") or 0.0,
        sources=sources,
        reason=final.get("reason"),  # see note below
        conversation_id=conversation_id,
    )


def ask_question(
    question: str,
    conversation_id: str,
    graph,
    conversation_history: list[dict[str, str]] | None = None,
    response_conversation_id: str | None = None,
) -> AskResponse:
    """
    Run a question through the full agent graph
    (Security -> Document -> Retrieval -> Confidence -> Answer ->
    Citation -> Validation) and return the validated response.

    Refusals (blocked by security, low confidence, or failed grounding
    validation) come back through the same graph output shape — the
    graph itself is responsible for populating a refusal "answer" and
    a confidence_score/sources that reflect the refusal. This service
    does not special-case refusals; it trusts the graph's gating logic
    per the architecture ground rules (hard short-circuit is enforced
    in the graph, not here).
    """
    if graph is None:
        raise GraphNotReadyError(
            "Compiled LangGraph is not wired up yet. "
            "Import the real graph in app/services/qa_service.py."
        )

    log_ctx = RequestLogContext(question)
    callback = PipelineLoggingCallback(log_ctx)
    thread_config = {"configurable": {"thread_id": conversation_id}}
    invoke_config = {
        **thread_config,
        "callbacks": [callback],
    }

    with _lock_for_conversation(conversation_id):
        try:
            if conversation_history is None:
                snapshot = graph.get_state(thread_config)
                previous_history = (snapshot.values or {}).get(
                    "conversation_history", []
                )[-(_MAX_MEMORY_MESSAGES - 2):]
            else:
                previous_history = conversation_history[-(_MAX_MEMORY_MESSAGES - 2):]

            result: Dict[str, Any] = graph.invoke(
                {
                    "question": question,
                    "conversation_history": previous_history,
                },
                config=invoke_config,
            )

            final = result.get("final_response") or {}
            updated_history = [
                *previous_history,
                {"role": "user", "content": question},
                {"role": "assistant", "content": final.get("answer") or ""},
            ][-_MAX_MEMORY_MESSAGES:]
            # Persist completed turns, including refusals, to the same thread.
            graph.update_state(
                thread_config, {"conversation_history": updated_history}
            )
        except Exception as exc:
            log_ctx.error = str(exc)
            log_ctx.finalize(error=str(exc))
            raise

    log_ctx.finalize(result)
    return _to_ask_response(result, response_conversation_id or conversation_id)
