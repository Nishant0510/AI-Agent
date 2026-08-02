# app/llm/ollama_client.py
"""
Thin wrapper around the Ollama client for Qwen2.5 inference.

Local dev note: OLLAMA_MODEL_TAG (e.g. "qwen2.5:7b-instruct") is the
actual quantized GGUF tag served by Ollama, which may differ from
LLM_MODEL in .env (the canonical HF model identity used for prompts/
citations/logs). That divergence is intentional for CPU-friendly local
dev — see README config notes if swapping to a transformers/vLLM
backend for closer prod parity.
"""
import logging

import ollama

from app.utils.config import settings

logger = logging.getLogger(__name__)

_client = ollama.Client(host=settings.ollama_host)


def generate(prompt: str, temperature: float = 0.1) -> str:
    """
    Sends a single prompt to the local Ollama-served Qwen2.5 model and
    returns the raw text response. Low temperature by default since
    this is a grounded-answer use case, not creative generation.
    """
    logger.info("Calling Ollama model=%s", settings.ollama_model_tag)
    response = _client.generate(
        model=settings.ollama_model_tag,
        prompt=prompt,
        options={"temperature": temperature},
    )
    return response["response"].strip()