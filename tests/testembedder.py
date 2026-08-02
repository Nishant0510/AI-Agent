from app.llm.embedder import embed_texts

vecs = embed_texts(["The sterilizer should be cleaned weekly.", "Do not immerse the power cord in water."])
print(vecs.shape)  # should be (2, 768) for bge-base