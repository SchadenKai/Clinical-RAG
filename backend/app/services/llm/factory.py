from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.config import settings


def get_llm_provider() -> BaseChatModel:
    return ChatOpenAI(model="chatgpt-4o-latest", api_key=settings.openai_api_key)
