from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.tokenizer import get_tokenizer_service
from app.services.llm.tokenizer import TokenizerService


@lru_cache
def get_chunker(
    app_settings: Annotated[Settings, Depends(get_app_settings)],
    tokenizer_service: Annotated[TokenizerService, Depends(get_tokenizer_service)],
) -> ChunkerService:
    return ChunkerService(
        app_settings=app_settings, tokenizer_service=tokenizer_service
    )
