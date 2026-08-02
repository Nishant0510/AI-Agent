# app/agent/nodes/retrieval_agent.py

import logging

from app.agent.state.schema import AgentState
from app.models.retrieval import RetrievalResult, RetrievedChunk
from app.vectorstore.faiss_store import search  
from app.llm.embedder import embed_query 
from app.utils.config import settings
from app.vectorstore.faiss_store import load_index

logger = logging.getLogger(__name__)

def retrieval_agent_node(state: AgentState) -> AgentState:
    print("\n========== RETRIEVAL AGENT ==========")
    print("searching for relevant chunks in FAISS index...")
    """
    Embeds the (already security-checked) question and searches FAISS for
    the top-K most similar chunks. Deduplicates near-identical chunks by
    chunk_id. Does NOT apply the similarity threshold — that decision
    belongs to the Confidence Agent's conditional edge, not here, to avoid
    duplicating the gate logic in two places.
    """
    question = state["question"]

    try:
        query_embedding = embed_query(question)
    except Exception:
        logger.exception("Embedding generation failed for query")
        return {
            **state,
            "retrieval_result": RetrievalResult(
                query=question,
                chunks=[],
            ),
        }

    try:
        findex, fchunks = load_index(settings.vector_db)

        raw_results = search(
            findex,
            fchunks,
            query_embedding,
            top_k=settings.top_k,
        )
    except Exception:
        logger.exception("FAISS similarity search failed")
        return {
            **state,
            "retrieval_result": RetrievalResult(
                query=question,
                chunks=[],
            ),
        }

    chunks: list[RetrievedChunk] = []
    seen_chunk_ids: set[str] = set()

    for chunk in raw_results:
        if chunk.chunk_id in seen_chunk_ids:
            continue

        seen_chunk_ids.add(chunk.chunk_id)
        chunks.append(chunk)

    chunks = chunks[: settings.max_context_chunks]

    retrieval_result = RetrievalResult(
        query=question,
        chunks=chunks,
    )

    logger.info(
        "Retrieval agent returned %d chunks, top_score=%.4f",
        len(chunks),
        retrieval_result.top_score,
    )

    print(f"Retrieved {len(chunks)} chunks")

    return {
        **state,
        "retrieval_result": retrieval_result,
    }


# def retrieval_agent_node(state: AgentState) -> AgentState:
#     """
#     Embeds the (already security-checked) question and searches FAISS for
#     the top-K most similar chunks. Deduplicates near-identical chunks by
#     chunk_id. Does NOT apply the similarity threshold — that decision
#     belongs to the Confidence Agent's conditional edge, not here, to avoid
#     duplicating the gate logic in two places.
#     """
#     question = state["question"]

#     try:
#         query_embedding = embed_query(question)
#     except Exception:
#         logger.exception("Embedding generation failed for query")
#         return {
#             **state,
#             "retrieval_result": RetrievalResult(chunks=[], top_score=0.0),
#         }

#     try:

#         findex, fchunks = load_index(settings.vector_db)

#         raw_results = search(
#             findex,
#             fchunks,
#             query_embedding,
#             top_k=settings.TOP_K,
#         )
#     except Exception:
#         logger.exception("FAISS similarity search failed")
#         return {
#             **state,
#             "retrieval_result": RetrievalResult(chunks=[], top_score=0.0),
#         }

#     chunks: list[RetrievedChunk] = []
#     seen_chunk_ids = set()

#     for result in raw_results:
#         chunk_id = result["chunk_id"]
#         if chunk_id in seen_chunk_ids:
#             continue
#         seen_chunk_ids.add(chunk_id)

#         chunks.append(
#             RetrievedChunk(
#                 document=result["document"],
#                 page=result["page"],
#                 chunk_id=chunk_id,
#                 similarity_score=result["similarity_score"],
#                 text=result["text"],
#             )
#         )

#     chunks = chunks[: settings.max_context_chunks]
#     top_score = max((c["similarity_score"] for c in chunks), default=0.0)

#     logger.info(
#         "Retrieval agent returned %d chunks, top_score=%.4f",
#         len(chunks),
#         top_score,
#     )

#     return {
#         **state,
#         "retrieval_result": RetrievalResult(chunks=chunks, top_score=top_score),
#     }