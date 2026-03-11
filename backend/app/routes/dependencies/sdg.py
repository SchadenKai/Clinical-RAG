from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from app.agent.sdg.main import agent
from app.core.config import Settings
from app.rag.embeddings import EmbeddingService
from app.routes.dependencies.embedding import get_embedding
from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.settings import get_app_settings
from app.services.file_store.db import S3Service
from app.services.llm.factory import ChatModelService
from app.services.sdg import SDGService


@lru_cache
def get_sdg_agent() -> CompiledStateGraph:
    return agent


def get_sdg_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
    llm_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding)],
    s3_service: Annotated[S3Service, Depends(get_s3_service)],
) -> SDGService:
    return SDGService(
        sdg_agent=get_sdg_agent(),
        llm_service=llm_service,
        embedding_service=embedding_service,
        s3_service=s3_service,
        settings=settings,
    )
