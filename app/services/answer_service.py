# app/services/answer_service.py
"""
Single-shot reference pipeline: retrieve -> build prompt -> generate.

This is the Phase 2 fallback implementation with NO confidence gating
and NO security checks — it exists to validate retrieval + prompting +
generation work end-to-end before those concerns are layered in as
separate LangGraph agents in Phase 3.

⚠️ Do not expose this directly via the /ask API endpoint once the
multi-agent graph exists — it skips the Security Agent and the
Confidence Agent's refusal gate, both of which are required guarantees
per project spec.
"""
import logging

from app.llm.ollama_client import generate
from app.models.retrieval import RetrievalResult
from app.prompts.grounded_answer import build_prompt
from app.retrieval.retriever import retrieve
from app.utils.config import settings

logger = logging.getLogger(__name__)


def answer_question(question: str) -> dict:
    """
    Naive end-to-end answer generation, matching the eventual API
    response shape so downstream code doesn't need to change:
    {"answer", "confidence_score", "sources"}.

    confidence_score here is just top_score from retrieval — it is
    NOT gated (no refusal logic). Phase 3's Confidence Agent replaces
    this with a real threshold check that can short-circuit before
    generation ever happens.
    """
    retrieval_result: RetrievalResult = retrieve(question, top_k=settings.top_k)

    if not retrieval_result.chunks:
        logger.warning("No chunks retrieved for question: %r", question)
        return {
            "answer": "I don't have enough information in the provided documentation to answer that.",
            "confidence_score": 0.0,
            "sources": [],
        }

    context_chunks = retrieval_result.chunks[: settings.max_context_chunks]
    prompt = build_prompt(question, context_chunks)
    raw_answer = generate(prompt)

    return {
        "answer": raw_answer,
        "confidence_score": retrieval_result.top_score,
        "sources": [
            {
                "document": c.document,
                "page": c.page,
                "chunk_id": c.chunk_id,
                "similarity_score": c.similarity_score,
            }
            for c in context_chunks
        ],
    }