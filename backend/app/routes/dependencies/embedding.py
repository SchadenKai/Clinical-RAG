from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.rag.embeddings import EmbeddingService
from app.routes.dependencies.settings import get_app_settings


@lru_cache
def get_embedding(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> EmbeddingService:
    # currently only designed for openai
    _config = {
        "api_key": settings.embedding_api_key,
        "model": settings.embedding_model,
        # "dimensions": settings.vector_dim,
        # "max_retries": 5,
        # "request_timeout": None,
    }
    return EmbeddingService(
        provider=settings.embedding_provider,
        config=_config,
        setting=settings,
    )
