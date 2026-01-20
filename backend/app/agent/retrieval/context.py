from langchain_core.language_models.chat_models import BaseChatModel
from langchain_text_splitters import TextSplitter
from pydantic import BaseModel, ConfigDict
from pymilvus import MilvusClient

from app.rag.embeddings import EmbeddingService
from app.services.llm.tokenizer import TokenizerService


class AgentContext(BaseModel):
    chunker: TextSplitter
    embedding: EmbeddingService
    tokenizer: TokenizerService
    db_client: MilvusClient
    collection_name: str
    chat_model: BaseChatModel
    include_generation: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)
