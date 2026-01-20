from functools import lru_cache

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_nebius.chat_models import ChatNebius
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.logger import app_logger


class ChatModelService:
    def __init__(self, provider, model_name, api_key):
        self._client: BaseChatModel | None = None
        self.provider: str = provider
        self.model_name: str = model_name
        self.api_key: str = api_key

    @property
    def client(self) -> BaseChatModel:
        if self._client:
            return self._client
        if self.provider == "openai":
            self._client = ChatOpenAI(
                model=self.model_name, api_key=settings.llm_api_key
            )
        elif self.provider == "anthropic":
            self._client = ChatAnthropic(
                model_name=self.model_name, api_key=settings.llm_api_key
            )
        elif self.provider == "nebius":
            self._client = ChatNebius(
                api_key=settings.llm_api_key,
                model=self.model_name,
            )
        elif self.provider == "gemini":
            self._client = ChatGoogleGenerativeAI(
                api_key=settings.llm_api_key, model=self.model_name
            )
        else:
            self._client = ChatOpenAI(model=self.model_name)
        app_logger.info(f"Selected model: {self._client.get_name()}")
        return self._client

    def test_chat_model(self) -> None:
        res = self.client.invoke("")
        app_logger.info(f"Testing chat model results: {res.content}")


@lru_cache
def get_chat_model_service() -> ChatModelService:
    return ChatModelService(
        provider=settings.llm_provider,
        model_name=settings.llm_model_name,
        api_key=settings.llm_api_key,
    )
