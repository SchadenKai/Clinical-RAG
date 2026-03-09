from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.core.config import settings
from app.logger import app_logger


class RerankScore(BaseModel):
    score: float = Field(
        description="Relevance score of the document to the query, from 0.0 to 10.0"
    )


class RerankerService:
    """
    Unified reranking service supporting multiple provider types:
    - 'llm': Use BaseChatModel via ChatModelService
    - 'slm': Use HuggingFace sentence-transformers CrossEncoder
    - 'milvus:<ranker_type>': Use Milvus BaseRanker (weighted, rrf, etc.)
    """

    MILVUS_RANKERS = {
        "weighted": "WeightedRanker",
        "rrf": "RRFRanker",
    }

    def __init__(
        self,
        provider: str,
        model_name: str,
        chat_model_service: "ChatModelService | None" = None,
        milvus_client: "MilvusClient | None" = None,
    ):
        self.provider = provider
        self.model_name = model_name
        self._chat_model_service = chat_model_service
        self._milvus_client = milvus_client
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
            ranker_type = self.provider.split(":", 1)[1]
            if ranker_type not in self.MILVUS_RANKERS:
                raise ValueError(
                    f"Unknown Milvus ranker: {ranker_type!r}. "
                    f"Valid options: {list(self.MILVUS_RANKERS.keys())}"
                )
            if self._milvus_client is None:
                raise ValueError("'milvus' provider requires milvus_client")
        else:
            raise ValueError(
                f"Unknown reranker provider: {self.provider!r}. "
                "Valid formats: 'llm', 'slm', 'milvus:weighted', 'milvus:rrf'"
            )

    @property
    def model(self):
        """Lazy-load the reranking model based on provider."""
        if self._model is not None:
            return self._model

        if self.provider == "slm":
            # Check HF API key availability at access time for private models
            if self._is_hf_auth_model() and not settings.hf_api_key:
                app_logger.warning(
                    f"Loading {self.model_name} without HF_API_KEY; may fail for private models"
                )
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)

        elif self.provider == "llm":
            # LLM provider doesn't preload a model; uses ChatModelService directly
            pass

        elif self.provider.startswith("milvus:"):
            ranker_type = self.provider.split(":", 1)[1]
            self._model = self._load_milvus_ranker(ranker_type)

        return self._model

    def _is_hf_auth_model(self) -> bool:
        """Check if model name suggests authentication is required."""
        # Simple heuristic: model names with "/" typically need auth (user/org patterns)
        return "/" in self.model_name

    def _load_milvus_ranker(self, ranker_type: str):
        """Load and instantiate Milvus ranker by type."""
        if ranker_type == "weighted":
            from pymilvus import WeightedRanker

            return WeightedRanker(weights={})
        elif ranker_type == "rrf":
            from pymilvus import RRFRanker

            return RRFRanker()
        # Can extend with more ranker types as needed
        return None

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """Rerank documents based on query using the configured provider."""
        if not documents:
            return documents

        if self.provider == "slm":
            return self._rerank_slm(query, documents, top_k)
        elif self.provider == "llm":
            return self._rerank_llm(query, documents, top_k)
        elif self.provider.startswith("milvus:"):
            return self._rerank_milvus(query, documents, top_k)

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
            prompt = (
                f"Query: '{query}'\n"
                f"Document: '{doc.get('text', '')[:2000]}'\n\n"
                "Evaluate the relevance of this document to the query. "
                "Provide a score from 0.0 to 10.0 where 10.0 is highly relevant."
            )
            try:
                res = structured_model.invoke([HumanMessage(content=prompt)])
                doc["rerank_score"] = res.score if res else 0.0
            except Exception as e:
                app_logger.error(f"LLM reranking failed for a document: {e}")
                doc["rerank_score"] = 0.0

        return sorted(docs, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[
            :top_k
        ]

    def _rerank_milvus(
        self, query: str, documents: list[dict], top_k: int
    ) -> list[dict]:
        """Milvus-based reranking using pymilvus BaseRanker subclasses."""
        ranker = self.model

        docs = [dict(d) for d in documents]

        # TODO: Implement based on specific Milvus ranker API
        # BaseRanker is abstract; concrete rankers (WeightedRanker, RRFRanker)
        # provide specific ranking logic. Implementation depends on how
        # Milvus rankers integrate with external similarity scores.
        # For now, return docs sorted by any existing score or order
        if "score" in docs[0]:
            return sorted(docs, key=lambda x: x.get("score", 0.0), reverse=True)[
                :top_k
            ]
        else:
            app_logger.warning(
                f"Milvus ranker {self.provider} implementation incomplete; returning docs in original order"
            )
            return docs[:top_k]
