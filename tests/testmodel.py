from types import SimpleNamespace
from unittest.mock import patch

from app.llm.provider import LLMProviderError, generate


def test_generate_dispatches_to_openai():
    with patch(
        "app.llm.provider.settings", SimpleNamespace(llm_provider="openai")
    ), patch(
        "app.llm.openai_client.generate", return_value="openai answer"
    ) as mock_generate:
        assert generate("Say hello") == "openai answer"

    mock_generate.assert_called_once_with("Say hello", temperature=0.1)


def test_generate_dispatches_to_ollama():
    with patch(
        "app.llm.provider.settings", SimpleNamespace(llm_provider="ollama")
    ), patch(
        "app.llm.ollama_client.generate", return_value="ollama answer"
    ) as mock_generate:
        assert generate("Say hello", temperature=0.3) == "ollama answer"

    mock_generate.assert_called_once_with("Say hello", temperature=0.3)


def test_generate_rejects_unknown_provider():
    with patch(
        "app.llm.provider.settings", SimpleNamespace(llm_provider="unknown")
    ):
        try:
            generate("Say hello")
        except LLMProviderError as error:
            assert "Unsupported LLM_PROVIDER" in str(error)
        else:
            raise AssertionError("Expected LLMProviderError")
