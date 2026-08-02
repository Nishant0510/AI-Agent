"""
LangGraph callback that automatically logs node entry/exit for every node
in the graph, plus a final request summary. Attach via `config={"callbacks": [...]}`
when invoking the graph, so no individual node needs to call the logger.
"""

from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from app.services.logging_service import RequestLogContext


class PipelineLoggingCallback(BaseCallbackHandler):
    def __init__(self, log_context: RequestLogContext):
        self.ctx = log_context

    def on_chain_start(self, serialized: dict, inputs: dict, *, run_id: UUID, tags: Optional[list] = None, **kwargs) -> None:
        node_name = (tags or ["unknown_node"])[0]
        self.ctx.log_node_start(node_name)

    def on_chain_end(self, outputs: dict, *, run_id: UUID, tags: Optional[list] = None, **kwargs) -> None:
        node_name = (tags or ["unknown_node"])[0]
        self.ctx.log_node_end(node_name, status="completed")

    def on_chain_error(self, error: BaseException, *, run_id: UUID, tags: Optional[list] = None, **kwargs) -> None:
        node_name = (tags or ["unknown_node"])[0]
        self.ctx.log_node_end(node_name, status="error", error=str(error))
        self.ctx.error = str(error)

    def on_llm_start(self, serialized: dict, prompts: list[str], *, run_id: UUID, **kwargs) -> None:
        self._llm_start_time = __import__("time").perf_counter()

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs) -> None:
        import time
        if hasattr(self, "_llm_start_time"):
            self.ctx.log_llm_latency(time.perf_counter() - self._llm_start_time)