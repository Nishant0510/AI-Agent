from openai import OpenAI

from app.utils.config import settings


def generate(prompt: str, temperature: float = 0.1) -> str:
    """Generate a response with the configured OpenAI model."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        temperature=temperature,
    )

    return response.output_text.strip()
