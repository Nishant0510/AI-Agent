from app.agent.state.schema import AgentState
 
# Return values match the edge labels used when wiring this into the graph,
# e.g.:
#
#   graph.add_conditional_edges(
#       "security_agent",
#       route_after_security,
#       {"blocked": END, "proceed": "document_agent"},
#   )
#
# This is what makes the block a hard code-level short-circuit rather than
# a prompt instruction: if is_safe is False, the graph literally does not
# have an edge to document_agent/retrieval_agent from here.
 
 
def route_after_security(state: AgentState) -> str:
    if not state["is_safe"]:
        return "blocked"
    return "proceed"
 