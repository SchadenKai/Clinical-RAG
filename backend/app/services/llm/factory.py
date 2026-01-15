from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI


def get_llm_provider() -> BaseChatModel:
    return ChatOpenAI(model="chatgpt-4o-latest")
