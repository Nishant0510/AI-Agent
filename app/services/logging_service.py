"""
Structured JSON logging service for the Philips Product Knowledge AI Agent.

Emits one JSON line per pipeline event (node enter/exit) and one summary
JSON line per completed request, to logs/app.jsonl.
"""

import json
import logging
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from app.utils.config import settings


class JsonFormatter(logging.Formatter):
    """Formats each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Anything passed via `extra={...}` gets merged in.
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _build_logger() -> logging.Logger:
    # Config has lowercase field names: settings.log_level
    log_dir = Path(getattr(settings, "log_dir", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    # Existing modules use logging.getLogger(__name__), e.g. "app.agent..."
    # Using "app" lets their logs propagate to these handlers.
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_dir / "app.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

        console = logging.StreamHandler()
        console.setFormatter(JsonFormatter())
        logger.addHandler(console)

    return logger


logger = _build_logger()


class RequestLogContext:
    """
    Tracks one request's lifecycle across the LangGraph run: node trace,
    timings, and the final summary fields required by Phase 6 spec.

    Usage: created once per request (e.g. in the /ask endpoint or a
    supervisor entry node), passed through state or held by the callback.
    """

    def __init__(self, question: str):
        self.request_id = str(uuid.uuid4())
        self.question = question
        self.start_time = time.perf_counter()
        self.node_trace: list[dict[str, Any]] = []
        self.llm_latency: Optional[float] = None
        self.error: Optional[str] = None

    def log_node_start(self, node_name: str) -> None:
        self.node_trace.append({
            "node": node_name,
            "started_at": time.perf_counter(),
            "status": "started",
        })

    def log_node_end(self, node_name: str, status: str = "completed", error: Optional[str] = None) -> None:
        for entry in reversed(self.node_trace):
            if entry["node"] == node_name and entry["status"] == "started":
                entry["duration_ms"] = round((time.perf_counter() - entry["started_at"]) * 1000, 2)
                entry["status"] = status
                del entry["started_at"]
                if error:
                    entry["error"] = error
                break

    def log_llm_latency(self, seconds: float) -> None:
        self.llm_latency = round(seconds * 1000, 2)  # store as ms

    def finalize(self, final_state: Optional[dict] = None, error: Optional[str] = None) -> None:
        """
        Extracts the fields the log needs from the graph's final AgentState
        and writes the summary line. Accepts the whole final_state so callers
        (e.g. the /ask route) don't need to know AgentState's internal shape.
        """
        final_state = final_state or {}

        retrieval_result = final_state.get("retrieval_result")
        retrieved_chunks = (
            [chunk.model_dump(exclude={"text"}) for chunk in retrieval_result.chunks]
            if retrieval_result
            else []
        )
        similarity_scores = [
            chunk["similarity_score"] for chunk in retrieved_chunks
        ]

        confidence_score = final_state.get("confidence_score")

        if error or final_state.get("refusal_reason") is None and final_state.get("decision") == "error":
            outcome = "error"
        elif final_state.get("decision") == "refuse":
            outcome = "refused"
        elif final_state.get("is_safe") is False:
            outcome = "blocked"
        else:
            outcome = "responded"

        total_ms = round((time.perf_counter() - self.start_time) * 1000, 2)
        logger.info(
            "request_completed",
            extra={"extra_fields": {
                "request_id": self.request_id,
                "question": self.question,
                "retrieved_chunks": retrieved_chunks,
                "similarity_scores": similarity_scores,
                "llm_latency_ms": self.llm_latency,
                "execution_time_ms": total_ms,
                "confidence_score": confidence_score,
                "outcome": outcome,
                "error": error or self.error,
                "node_trace": self.node_trace,
            }},
        )