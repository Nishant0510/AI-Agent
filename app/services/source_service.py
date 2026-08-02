
# app/services/source_service.py

"""
Lists currently ingested documents from the FAISS vector store
for the GET /sources endpoint.
"""

from typing import List

from app.models.schemas import SourceDocument
from app.vectorstore.store import list_documents


def list_ingested_sources() -> List[SourceDocument]:
    """
    Return metadata for each unique document currently stored in the
    vector database.

    If no vector database exists yet, an empty list is returned.
    """
    return list_documents()



# #app/services/source_service.py
# """
# Lists currently ingested documents from the FAISS vector store's
# metadata, for GET /sources.

# NOTE: Assumes app/vectorstore exposes a method to enumerate unique
# source documents from the persisted index metadata. If that method
# doesn't exist yet, add `list_documents()` to your vectorstore module
# matching the TODO below.
# """

# from typing import List
# from app.vectorstore.store import list_documents
# from app.models.schemas import SourceDocument

# # TODO: import the real vector store accessor, e.g.:
# # from app.vectorstore.store import get_vectorstore
# get_vectorstore = None  # placeholder


# def list_ingested_sources() -> List[SourceDocument]:
#     """
#     Return metadata for each unique document currently in the FAISS
#     index. Returns an empty list if no vector DB exists yet (mirrors
#     the "No documents found" troubleshooting case in the README).
#     """
#     if get_vectorstore is None:
#         # No vectorstore wired up yet — behave like an empty index
#         # rather than crashing the endpoint.
#         return []

#     store = get_vectorstore()
#     # Expected shape: store.list_documents() -> List[dict] with
#     # keys "document", "num_chunks", "last_ingested_at"
#     raw_docs = store.list_documents()
#     return [
#         SourceDocument(
#             document=d["document"],
#             num_chunks=d.get("num_chunks"),
#             last_ingested_at=d.get("last_ingested_at"),
#         )
#         for d in raw_docs
#     ]