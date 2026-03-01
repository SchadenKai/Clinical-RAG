from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.dependencies.auth import get_current_user
from app.routes.dependencies.settings_service import get_settings_service
from app.services.settings_service import SettingsService

settings_router = APIRouter(prefix="/settings", tags=["settings"])


class LLMConfigPayload(BaseModel):
    provider: str
    model_name: str
    api_key: str


class EmbeddingConfigPayload(BaseModel):
    provider: str
    model_name: str
    api_key: str


@settings_router.get("/llm")
def get_llm_settings(
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    config = settings_service.get_active_llm_config()
    if not config:
        return {}
    return {
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": "***",
    }


@settings_router.put("/llm")
def update_llm_settings(
    payload: LLMConfigPayload,
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    settings_service.update_llm_config(
        provider=payload.provider,
        model_name=payload.model_name,
        api_key=payload.api_key,
    )
    return {"message": "LLM configuration updated successfully"}


@settings_router.get("/embedding")
def get_embedding_settings(
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    config = settings_service.get_active_embedding_config()
    if not config:
        return {}
    return {
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": "***",
    }


@settings_router.put("/embedding", status_code=202)
def update_embedding_settings(
    payload: EmbeddingConfigPayload,
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    result = settings_service.update_embedding_config(
        provider=payload.provider,
        model_name=payload.model_name,
        api_key=payload.api_key,
    )
    return {
        "message": result["message"],
        "documents_affected": result["documents_affected"],
    }


@settings_router.get("/config")
def get_system_config():
    from app.core.config import settings
    return {"dev_mode": settings.dev_mode}
