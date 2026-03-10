from app.core.config import settings
from app.rag.db import VectorClient


# embedding and creation of final docs
def get_final_document(
    vector_name: str, text_name: str, documents: list[dict], vectors: list
) -> list[dict]:
    final_doc_list = []
    for i, doc in enumerate(documents):
        final_doc = dict(doc)
        final_doc[vector_name] = vectors[i]
        final_doc_list.append(final_doc)
    return final_doc_list


# storage
def store_documents(documents: list[dict], vector_db: VectorClient) -> None:
    db = vector_db.client
    db.insert(collection_name=settings, data=documents)
