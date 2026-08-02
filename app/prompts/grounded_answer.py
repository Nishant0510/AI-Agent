# app/prompts/grounded_answer.py
"""
Strict grounding prompt template. The LLM is instructed to answer
ONLY from the provided context chunks and to explicitly say it
doesn't know if the answer isn't present. This is a defense-in-depth
layer, not the primary grounding guarantee — Retrieval/Confidence/
Validation agents enforce grounding in code, this just constrains
generation itself.
"""
from app.models.retrieval import RetrievedChunk

SYSTEM_INSTRUCTIONS = """You are a Philips product documentation assistant.

Rules you MUST follow:
1. Answer ONLY using the information in the provided context below.
2. Do NOT use any outside knowledge, even if you are confident about it.
3. If the context does not contain enough information to answer the
   question, respond exactly with: "I don't have enough information in
   the provided documentation to answer that."
4. When you state a fact, keep it traceable to a specific context chunk
   below — do not blend in unstated assumptions.
5. Be concise and factual. Do not speculate.
"""


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Formats retrieved chunks into a numbered context block with citations."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[Chunk {i}] (Source: {chunk.document}, Page: {chunk.page}, "
            f"Chunk ID: {chunk.chunk_id})\n{chunk.text}"
        )
    return "\n\n".join(blocks)


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = format_context(chunks)
    return f"""{SYSTEM_INSTRUCTIONS}

Context:
{context}

Question: {question}

Answer:"""