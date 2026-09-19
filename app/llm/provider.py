"""Provider-neutral LLM generation entry point."""

from app.utils.config import settings


class LLMProviderError(ValueError):
    """Raised when the configured LLM provider is not supported."""


def generate(prompt: str, temperature: float = 0.1) -> str:
    """Generate text using the LLM selected by ``LLM_PROVIDER``.

    Imports are deliberately lazy so selecting one provider does not require
    the other provider's client or credentials to be initialized.
    """
    provider = settings.llm_provider.strip().lower()

    if provider == "openai":
        from app.llm.openai_client import generate as openai_generate

        return openai_generate(prompt, temperature=temperature)

    if provider == "ollama":
        from app.llm.ollama_client import generate as ollama_generate

        return ollama_generate(prompt, temperature=temperature)

    raise LLMProviderError(
        f"Unsupported LLM_PROVIDER {settings.llm_provider!r}. "
        "Supported values are 'openai' and 'ollama'."
    )
