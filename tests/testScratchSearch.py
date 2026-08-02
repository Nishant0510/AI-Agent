from pathlib import Path
from app.vectorstore.faiss_store import load_index, search
from app.llm.embedder import embed_query

VECTOR_DB_PATH = Path("data/vector_db")

index, chunks = load_index(VECTOR_DB_PATH)
print(f"Loaded index with {index.ntotal} vectors, {len(chunks)} metadata entries")

query = "What is Device Warmup in simply Go Device?"
query_embedding = embed_query(query)

results = search(index, chunks, query_embedding, top_k=5)

for chunk, score in results:
    print(f"\n--- score={score:.4f} | {chunk.metadata.document_name} | page {chunk.metadata.page_number} ---")
    print(chunk.text[:300])