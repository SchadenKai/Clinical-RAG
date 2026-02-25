import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", frozen=True, extra="ignore")

    dev_mode: bool = (
        True if str(os.environ.get("DEV_MODE")).lower() == "true" else False
    )

    app_title: str = "Clinical Guideline RAG Service (CDC/WHO)"
    app_version: str = "v0.1.0"
    timezone: str = "Asia/Manila"

    # NOTE: temporarily made this optional for the testing to pass
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    llm_api_key: str = os.environ.get("LLM_API_KEY", openai_api_key)
    llm_provider: str = os.environ.get("LLM_PROVIDER", "openai")
    llm_model_name: str = os.environ.get("LLM_MODEL_NAME", "gpt-4o")

    milvus_url: str = os.environ.get("MILVUS_URL", "http://localhost:19530")
    milvus_db_name: str = os.environ.get("MILVUS_DB_NAME", "cdc_rag")
    milvus_collection_name: str = os.environ.get("MILVUS_COLLECTION_NAME", "test")
    milvus_user: str = os.environ.get("MILVUS_USER", "root")
    milvus_password: str = os.environ.get("MILVUS_PASSWORD", "Milvus")
    milvus_token: str = os.environ.get("MILVUS_TOKEN", "")

    # vector config
    vector_dim: int = 3584
    text_field_max_length: int = 2048
    chunk_strategy: str = "hybrid_hierarchal"
    chunk_size: int = 1024
    chunk_overlap: int = 0
    lowest_score_threshold: float = 0.6
    highest_score_threshold: float = 1.0

    rag_metrics_threshold: float = 0.7

    # model config
    embedding_provider: str = os.environ.get("EMBEDDING_PROVIDER", "openai")
    embedding_api_key: str = os.environ.get("EMBEDDING_API_KEY", "")
    embedding_model: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

    hf_api_key: str = os.environ.get("HUGGING_FACE_API_KEY", "")

    # object store
    minio_endpoint_url: str = os.environ.get(
        "MINIO_ENDPOINT_URL", "http://localhost:9000"
    )
    minio_username: str = os.environ.get("MINIO_USERNAME", "abcd")
    minio_password: str = os.environ.get("MINIO_PASSWORD", "abcd2345")
    minio_bucket_name: str = os.environ.get("MINO_BUCKET_NAME", "default")


settings = Settings()
