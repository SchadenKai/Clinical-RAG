from docling_core.transforms.chunker.base import BaseChunker
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict
from pymilvus import MilvusClient

from app.core.config import Settings
from app.rag.embeddings import EmbeddingService
from app.services.llm.tokenizer import TokenizerService
from app.services.reranking import RerankerService


class AgentContext(BaseModel):
    chunker: BaseChunker
    embedding: EmbeddingService
    tokenizer: TokenizerService
    db_client: MilvusClient
    chat_model: BaseChatModel
    reranker: RerankerService
    include_generation: bool = False
    settings: Settings

    model_config = ConfigDict(arbitrary_types_allowed=True)
