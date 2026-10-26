"""Use Jev to decide whether a query needs product-document retrieval."""

import logging

import httpx

from app.agent.state.schema import AgentState
from app.utils.config import settings

logger = logging.getLogger(__name__)


def decision_agent_node(state: AgentState) -> AgentState:
    """Route brief conversational messages around RAG.

    If Jev is unavailable or returns an unexpected answer, default to RAG so
    product answers still pass through the existing evidence and confidence
    gates.
    """
    if not settings.jev_api_key:
        logger.warning("Jev API key is missing; routing query through RAG")
        return {**state, "rag_decision": "use_rag"}

    payload = {
        "model": settings.jev_model,
        "state": {
            "question": state["question"],
            "recent_conversation": state.get("conversation_history", [])[-6:],
        },
        "questions": {
            "route": {
                "type": "choice",
                "instructions": (
                    "Choose direct_llm only for greetings, thanks, or brief social "
                    "messages that do not ask for product facts. Choose use_rag "
                    "for all substantive questions, including Philips product "
                    "features, setup, troubleshooting, safety, compatibility, and "
                    "questions outside the supported product scope."
                ),
                "criteria": {
                    "direct_llm": "A greeting or short social message, with no factual request.",
                    "use_rag": "Any substantive question or request for information.",
                },
            }
        },
    }

    try:
        response = httpx.post(
            settings.jev_api_url,
            headers={"Authorization": f"Bearer {settings.jev_api_key}"},
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        choice = response.json()["answers"]["route"]["choice"]
        if choice not in {"direct_llm", "use_rag"}:
            raise ValueError(f"Unexpected Jev routing choice: {choice!r}")
        return {**state, "rag_decision": choice}
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        logger.exception("Jev routing failed; routing query through RAG")
        return {**state, "rag_decision": "use_rag"}


def route_after_decision(state: AgentState) -> str:
    return "direct_llm" if state.get("rag_decision") == "direct_llm" else "use_rag"


def direct_llm_response_node(state: AgentState) -> AgentState:
    """Answer conversational messages with the configured LLM, without RAG."""
    from app.llm.provider import generate

    recent_turns = state.get("conversation_history") or []
    history = "\n".join(
        f"{turn.get('role', 'user')}: {turn.get('content', '')}"
        for turn in recent_turns[-6:]
    )
    prompt = f"""You are the conversational assistant for a Philips product knowledge application.
Reply naturally and concisely to the user's message. This route is for greetings,
thanks, and brief social messages. Do not invent or provide Philips product facts;
product questions must be answered from the product documentation through RAG.

Recent conversation (may be empty):
{history or "(none)"}

User message:
{state['question']}

Assistant reply:"""
    answer = generate(prompt, temperature=0.5)
    return {
        **state,
        "answer": answer,
        "sources": [],
        "confidence_score": None,
        "final_response": {
            "answer": answer,
            "confidence_score": None,
            "sources": [],
            "reason": "direct_llm",
        },
    }
