from typing import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings
from app.services.rag import RetrievalService


class AgentContext(BaseModel):
    llm: BaseChatModel = Field(
        description="Class to be used to interact with different LLMs. \
            Need to pass appropriate parameters for your model provider of choice.",
    )
    tools: list[Callable | BaseTool] = Field(
        default_factory=list,
        description="List of tools available to this agent runtime.",
    )
    retrieval_service: RetrievalService = Field(
        default=None, description="RetrievalService instance for RAG-enabled agents."
    )
    settings: Settings = Field(description="Application settings instance.")

    model_config = ConfigDict(arbitrary_types_allowed=True)
