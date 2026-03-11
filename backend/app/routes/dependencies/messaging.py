from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from app.core.config import Settings
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.routes.dependencies.embedding import get_embedding
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.react_agent import get_react_agent
from app.routes.dependencies.reranking import get_reranker_service
from app.routes.dependencies.retriever_agent import get_retriever_agent
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.tokenizer import get_tokenizer_service
from app.routes.dependencies.vector_db import get_vector_client
from app.services.llm.factory import ChatModelService
from app.services.llm.tokenizer import TokenizerService
from app.services.messaging import SendMessageService
from app.services.reranking import RerankerService


@lru_cache
def get_send_message_service(
    retriever_agent: Annotated[CompiledStateGraph, Depends(get_retriever_agent)],
    react_agent: Annotated[CompiledStateGraph, Depends(get_react_agent)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding)],
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    reranker_service: Annotated[RerankerService, Depends(get_reranker_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SendMessageService:
    return SendMessageService(
        retriever_agent=retriever_agent,
        react_agent=react_agent,
        embedding_service=embedding_service,
        vector_db_service=vector_db,
        tokenizer_service=tokenizer,
        chat_model_service=chat_model_service,
        reranker_service=reranker_service,
        settings=settings,
    )
