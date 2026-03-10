from docling_core.transforms.chunker.base import BaseChunker
from pydantic import BaseModel, ConfigDict
from pymilvus import MilvusClient

from app.core.config import Settings
from app.rag.embeddings import EmbeddingService
from app.services.file_store.db import S3Service
from app.services.llm.tokenizer import TokenizerService


class AgentContext(BaseModel):
    chunker: BaseChunker
    embedding: EmbeddingService
    s3_service: S3Service
    tokenizer: TokenizerService
    db_client: MilvusClient
    settings: Settings

    model_config = ConfigDict(arbitrary_types_allowed=True)
