from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_title: Optional[str] = "Clinical Guideline RAG Service (CDC/WHO)"
    app_version: Optional[str] = "v0.1.0"


settings = Settings()
