from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.chat import ChatRepository
from app.routes.dependencies.chat_agent import get_chat_agent
from app.routes.dependencies.db_session import get_db
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.rag import get_retrieval_service
from app.routes.dependencies.settings import get_app_settings
from app.services.chat import ChatService
from app.services.llm.factory import ChatModelService
from app.services.rag import RetrievalService


@lru_cache
def get_chat_service(
    db: Annotated[Session, Depends(get_db)],
    chat_agent: Annotated[CompiledStateGraph, Depends(get_chat_agent)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ChatService:
    return ChatService(
        chat_repository=ChatRepository(db),
        chat_agent=chat_agent,
        retrieval_service=retrieval_service,
        chat_model_service=chat_model_service,
        settings=settings,
    )
