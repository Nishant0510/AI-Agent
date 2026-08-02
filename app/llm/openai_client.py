from openai import OpenAI

from app.utils.config import settings

client = OpenAI(api_key=settings.openai_api_key)


def generate(prompt: str, temperature: float = 0.1) -> str:
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        temperature=temperature,
    )

    return response.output_text.strip()