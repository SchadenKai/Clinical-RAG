import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_title: str = "Clinical Guideline RAG Service (CDC/WHO)"
    app_version: str = "v0.1.0"

    openai_api_key: str = os.environ.get("OPENAI_API_KEY")

    milvus_url: str = os.environ.get("MILVUS_URL", "http://localhost:19530")
    milvus_db_name: str = os.environ.get("MILVUS_DB_NAME", "cdc_rag")
    milvus_collection_name: str = os.environ.get("MILVUS_COLLECTION_NAME", "test")
    milvus_user: str = os.environ.get("MILVUS_USER", "root")
    milvus_password: str = os.environ.get("MILVUS_PASSWORD", "Milvus")

    # vector config
    vector_dim: int = 512
    text_field_max_length: int = 2048

    # model config
    bi_encoder_model: str = "text-embedding-3-small"


settings = Settings()
