from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.routes.dependencies.chunker import get_chunker
from app.routes.dependencies.embedding import get_embedding
from app.routes.dependencies.indexing_agent import get_indexing_agent
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.retriever_agent import get_retriever_agent
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.tokenizer import get_tokenizer_service
from app.routes.dependencies.vector_db import get_vector_client
from app.services.llm.factory import ChatModelService
from app.services.llm.tokenizer import TokenizerService
from app.services.rag import IndexingService, RetrievalService


@lru_cache
def get_retrieval_service(
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding)],
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    retriever_agent: Annotated[CompiledStateGraph, Depends(get_retriever_agent)],
    chunker_service: Annotated[ChunkerService, Depends(get_chunker)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> RetrievalService:
    return RetrievalService(
        embedding_service=embedding_service,
        vector_db_service=vector_db,
        tokenizer_service=tokenizer,
        chat_model_service=chat_model_service,
        retriever_agent=retriever_agent,
        chunker_service=chunker_service,
        settings=settings,
    )


def get_indexing_service(
    chunker_service: Annotated[ChunkerService, Depends(get_chunker)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding)],
    vector_db_service: Annotated[VectorClient, Depends(get_vector_client)],
    tokenizer_service: Annotated[TokenizerService, Depends(get_tokenizer_service)],
    indexing_agent: Annotated[CompiledStateGraph, Depends(get_indexing_agent)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> IndexingService:
    return IndexingService(
        chunker_service=chunker_service,
        embedding_service=embedding_service,
        vector_db_service=vector_db_service,
        tokenizer_service=tokenizer_service,
        indexing_agent=indexing_agent,
        settings=settings,
    )

def get_indexing_service_manual() -> IndexingService:
    chunker_service = get_chunker()
    settings = get_app_settings()
    embedding_service = get_embedding(settings)
    tokenizer_service = get_tokenizer_service(settings)
    vector_db_service = get_vector_client(embedding_service, tokenizer_service)
    indexing_agent = get_indexing_agent()
    return IndexingService(
        chunker_service=chunker_service,
        embedding_service=embedding_service,
        vector_db_service=vector_db_service,
        tokenizer_service=tokenizer_service,
        indexing_agent=indexing_agent,
        settings=settings,
    )