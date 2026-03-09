from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.rag.db import VectorClient
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.vector_db import get_vector_client
from app.services.llm.factory import ChatModelService
from app.services.reranking import RerankerService


def get_reranker_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    vector_client: Annotated[VectorClient, Depends(get_vector_client)],
) -> RerankerService:
    """
    Factory for RerankerService with provider-specific dependencies.

    Supports two provider types:
    - 'llm': Uses ChatModelService (requires llm_api_key from settings)
    - 'slm': Uses HuggingFace CrossEncoder (requires hf_api_key for private models)
    """
    return RerankerService(
        provider=settings.reranker_provider,
        model_name=settings.reranker_model,
        hf_api_key=settings.hf_api_key,
        chat_model_service=chat_model_service
        if settings.reranker_provider == "llm"
        else None,
        milvus_client=vector_client.client
        if settings.reranker_provider.startswith("milvus")
        else None,
    )
