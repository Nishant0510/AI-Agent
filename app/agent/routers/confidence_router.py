from app.agent.state.schema import AgentState


def route_on_confidence(state: AgentState) -> str:
    """Pure routing function — no side effects, no LLM calls."""
    return state["decision"]