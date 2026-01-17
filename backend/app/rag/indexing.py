from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import TextSplitter

from app.core.config import settings
from app.rag.db import VectorClient

# document loader (of markdown / pdf)


# chunker
def get_chunked_text(text: str, chunker: TextSplitter) -> list[Document]:
    return chunker.split_text(text)


# embedding and creation of final docs
def get_final_document(
    vector_name: str, text_name: str, documents: list[Document], encoder: Embeddings
) -> list[dict]:
    final_doc_list = []
    for doc in documents:
        final_doc = doc.to_json()
        final_doc[vector_name] = encoder.embed_query(final_doc[text_name])
        final_doc_list.append(final_doc)
    return final_doc_list


# storage
def store_documents(documents: list[dict], vector_db: VectorClient) -> None:
    db = vector_db.client
    db.insert(collection_name=settings, data=documents)
