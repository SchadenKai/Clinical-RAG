from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.routes.dependencies.settings import get_app_settings
from app.services.llm.tokenizer import TokenizerService


@lru_cache
def get_tokenizer_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TokenizerService:
    return TokenizerService(
        model=settings.llm_model_name,
        embedding=settings.embedding_model,
        model_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
    )
