from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_nebius.chat_models import ChatNebius
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel, Field

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
        elif self.provider == "openrouter":
            self._client = ChatOpenRouter(
                api_key=settings.llm_api_key, model=self.model_name
            )
        else:
            self._client = ChatOpenAI(model=self.model_name)
        app_logger.info(f"Selected model: {self._client.get_name()}")
        return self._client

        def test_chat_model(self) -> None:
            res = self.client.invoke("")
            app_logger.info(f"Testing chat model results: {res.content}")


class RerankScore(BaseModel):
    score: float = Field(
        description="Relevance score of the document to the query, from 0.0 to 10.0"
    )


class RerankerService:
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self._slm_model = None

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        if not documents:
            return documents

        if self.provider == "slm":
            if not self._slm_model:
                from sentence_transformers import CrossEncoder

                self._slm_model = CrossEncoder(self.model_name)

            pairs = [[query, doc.get("text", "")] for doc in documents]
            scores = self._slm_model.predict(pairs)

            for i, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[i])

            documents.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return documents[:top_k]

        elif self.provider == "llm":
            chat_service = ChatModelService(
                provider=settings.llm_provider,
                model_name=self.model_name,
                api_key=self.api_key or settings.llm_api_key,
            )
            chat_model = chat_service.client
            structured_model = chat_model.with_structured_output(schema=RerankScore)

            for doc in documents:
                prompt = (
                    f"Query: '{query}'\n"
                    f"Document: '{doc.get('text', '')[:2000]}'\n\n"
                    "Evaluate the relevance of this document to the query. "
                    "Provide a score from 0.0 to 10.0 where 10.0 is highly relevant."
                )
                from langchain_core.messages import HumanMessage

                try:
                    res = structured_model.invoke([HumanMessage(content=prompt)])
                    doc["rerank_score"] = res.score if res else 0.0
                except Exception as e:
                    app_logger.error(f"LLM reranking failed for a document: {e}")
                    doc["rerank_score"] = 0.0

            documents.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return documents[:top_k]
        else:
            app_logger.warning(
                f"Unknown reranker provider: {self.provider}. Returning original documents."
            )
            return documents[:top_k]
