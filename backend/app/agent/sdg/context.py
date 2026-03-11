from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.rag.embeddings import EmbeddingService
from app.services.file_store.db import S3Service
from app.services.llm.factory import ChatModelService


class AgentContext(BaseModel):
    llm_service: ChatModelService
    embedding_service: EmbeddingService
    s3_service: S3Service
    settings: Settings

    model_config = ConfigDict(arbitrary_types_allowed=True)
