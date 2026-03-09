from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.logger import app_logger

if TYPE_CHECKING:
    from pymilvus import MilvusClient

    from app.services.chat_models import ChatModelService


class RerankScore(BaseModel):
    score: float = Field(
        description="Relevance score of the document to the query, from 0.0 to 10.0"
    )


class RerankerService:
    """
    Unified reranking service supporting multiple provider types:
    - 'llm': Use BaseChatModel via ChatModelService
    - 'slm': Use HuggingFace sentence-transformers CrossEncoder
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        chat_model_service: "ChatModelService | None" = None,
        milvus_client: "MilvusClient | None" = None,
        hf_api_key: str = "",
    ):
        self.provider = provider
        self.model_name = model_name
        self._chat_model_service = chat_model_service
        self._milvus_client = milvus_client
        self._hf_api_key = hf_api_key
        self._model = None

        # Basic validation at initialization time
        self._validate_provider()

    def _validate_provider(self) -> None:
        """Validate provider format and required dependencies."""
        if self.provider == "llm":
            if self._chat_model_service is None:
                raise ValueError("'llm' provider requires chat_model_service")
        elif self.provider == "slm":
            # SLM validation happens lazily when model property is accessed
            pass
        elif self.provider.startswith("milvus:"):
            raise ValueError(
                "Milvus reranking provider is not yet implemented. "
                "Valid providers: 'llm', 'slm'"
            )
        else:
            raise ValueError(
                f"Unknown reranker provider: {self.provider!r}. "
                "Valid formats: 'llm', 'slm'"
            )

    @property
    def model(self):
        """Lazy-load the reranking model based on provider."""
        if self._model is not None:
            return self._model

        if self.provider == "slm":
            if not self._hf_api_key:
                app_logger.debug(
                    f"Loading {self.model_name} without HF_API_KEY; "
                    "private models will fail"
                )
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)

        elif self.provider == "llm":
            # LLM provider uses ChatModelService directly; no preloaded model object.
            raise AttributeError(
                "The 'model' property is not available for the 'llm' provider. "
                "Use the internal ChatModelService via _rerank_llm instead."
            )

        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """Rerank documents based on query using the configured provider."""
        if not documents:
            return documents

        if self.provider == "slm":
            return self._rerank_slm(query, documents, top_k)
        elif self.provider == "llm":
            return self._rerank_llm(query, documents, top_k)

    def _rerank_slm(self, query: str, documents: list[dict], top_k: int) -> list[dict]:
        """SLM-based reranking using sentence-transformers CrossEncoder."""
        docs = [dict(d) for d in documents]
        pairs = [[query, doc.get("text", "")] for doc in docs]
        scores = self.model.predict(pairs)

        for i, doc in enumerate(docs):
            doc["rerank_score"] = float(scores[i])

        return sorted(docs, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[
            :top_k
        ]

    def _rerank_llm(self, query: str, documents: list[dict], top_k: int) -> list[dict]:
        """LLM-based reranking using ChatModelService with structured output."""
        chat_model = self._chat_model_service.client
        structured_model = chat_model.with_structured_output(schema=RerankScore)

        docs = [dict(d) for d in documents]
        for doc in docs:
            try:
                res = structured_model.invoke(
                    [
                        SystemMessage(
                            content=(
                                "You are a relevance scoring assistant. "
                                "Given a query and a document, evaluate how "
                                "relevant the document is to the query. "
                                "Provide a score from 0.0 to 10.0 where "
                                "10.0 is highly relevant."
                            )
                        ),
                        HumanMessage(
                            content=(
                                f"Query: {query}\n\n"
                                f"Document:\n{doc.get('text', '')[:2000]}"
                            )
                        ),
                    ]
                )
                doc["rerank_score"] = res.score if res else 0.0
            except Exception as e:
                app_logger.error(f"LLM reranking failed for a document: {e}")
                doc["rerank_score"] = 0.0

        return sorted(docs, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[
            :top_k
        ]
