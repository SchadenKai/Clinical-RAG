from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient, get_vector_client
from app.rag.embeddings import EmbeddingService, get_embedding
from app.routes.dependencies.chunker import get_chunker
from app.routes.dependencies.indexing_agent import get_indexing_agent
from app.routes.dependencies.retriever_agent import get_retriever_agent
from app.routes.dependencies.settings import get_app_settings
from app.services.llm.factory import ChatModelService, get_chat_model_service
from app.services.llm.tokenizer import TokenizerService, get_tokenizer_service
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
