"""
Thin service layer that invokes the compiled LangGraph agent pipeline
for question answering.

This module is intentionally the ONLY place that adapts between the
FastAPI request/response shape and the LangGraph state schema. If the
real GraphState differs from the minimal contract assumed here
(a dict with "question", "answer", "confidence_score", "sources"),
update the mapping in `_to_ask_response` only.
"""

from typing import Any, Dict
from app.agent.graph.callback import PipelineLoggingCallback
from app.services.logging_service import RequestLogContext

from app.models.schemas import AskResponse, SourceChunk

# TODO: import the actual compiled graph once available, e.g.:
from app.agent.graph.build_graph import compiled_graph
#compiled_graph = None  # placeholder — replace with real compiled LangGraph


class GraphNotReadyError(RuntimeError):
    """Raised when the compiled graph has not been initialized."""




def _to_ask_response(graph_output: Dict[str, Any]) -> AskResponse:
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
    )


def ask_question(question: str) -> AskResponse:
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
    if compiled_graph is None:
        raise GraphNotReadyError(
            "Compiled LangGraph is not wired up yet. "
            "Import the real graph in app/services/qa_service.py."
        )

    log_ctx = RequestLogContext(question)
    callback = PipelineLoggingCallback(log_ctx)

    try:
        result: Dict[str, Any] = compiled_graph.invoke(
            {"question": question},
            config={"callbacks": [callback]},
        )
    except Exception as exc:
        log_ctx.error = str(exc)
        log_ctx.finalize(error=str(exc))
        raise

    log_ctx.finalize(result)
    return _to_ask_response(result)