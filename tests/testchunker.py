from app.ingestion.chunker import chunk_document

chunks = chunk_document("data/users/SimplyGo-Usermanual.pdf", pages)
print(f"{len(chunks)} chunks created")
print(chunks[0].metadata)
print(chunks[0].text)