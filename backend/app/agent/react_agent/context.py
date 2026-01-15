from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    llm: BaseChatModel = Field(
        default=None,
        description="Class to be used to interact with different LLMs. \
            Need to pass appropriate parameters for your model provider of choice.",
    )
