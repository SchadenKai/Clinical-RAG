import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_title: str | None = "Clinical Guideline RAG Service (CDC/WHO)"
    app_version: str | None = "v0.1.0"

    openai_api_key: str = os.environ.get("OPENAI_API_KEY")


settings = Settings()
