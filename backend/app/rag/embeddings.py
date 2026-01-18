import time
from functools import lru_cache
from logging import Logger

from langchain_core.embeddings import Embeddings, FakeEmbeddings
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings

from app.core.config import Settings, settings
from app.logger import app_logger
from app.rag.models import EmbeddingResponseModel
from app.services.llm.calculate_cost import calculate_cost

# TODO: replace this with adapter
from app.services.llm.tokenizer import TokenizerService


# TODO: check if this is the best way to import deps
class EmbeddingService:
    def __init__(self, provider, config, setting, logger):
        self._client: Embeddings | None = None
        self.provider: str = provider
        self.config: dict = config
        self.settings: Settings = setting
        self.logger: Logger = logger

    @property
    def client(self) -> Embeddings:
        if self._client is None:
            if self.provider == "openai":
                self._client = OpenAIEmbeddings(**self.config)
            elif self.provider == "gemini":
                self._client = GoogleGenerativeAIEmbeddings(**self.config)
            elif self.provider == "azure":
                self._client = AzureOpenAIEmbeddings(**self.config)
            # only make this available during development
            elif self.provider == "fake":
                self._client = FakeEmbeddings(**self.config)
            elif self.provider == "nomic":
                self._client = NomicEmbeddings(**self.config)
            else:
                self._client = OpenAIEmbeddings(**self.config)
        return self._client

    def test_client_on_startup(self) -> None:
        try:
            self.client.embed_query("test")
        except Exception as e:
            raise Exception(f"Something went wrong: {e}") from e

    def embed_query(self, text: str, tokenizer: TokenizerService) -> list[float]:
        start_time = time.time()

        embed = self.client
        result_vector = embed.embed_query(text)
        duration_ms = (time.time() - start_time) * 1000  # convert seconds to ms

        # TODO: Make this non IO blocking
        token_cnt = tokenizer.compute_token_cnt(text)
        _, _, total_cost = calculate_cost(
            model_name=self.settings.llm_model_name,
            input_token=token_cnt,
        )
        return EmbeddingResponseModel(
            embeding=result_vector,
            token_count=token_cnt,
            total_cost=total_cost,
            duration_ms=duration_ms,
        )

    def embed_documents(
        self, documents: list[str], tokenizer: TokenizerService
    ) -> list[float]:
        start_time = time.time()
        embed = self.client
        result_vector = embed.embed_documents(documents)
        duration_ms = (time.time() - start_time) * 1000  # convert seconds to ms

        # TODO: Make this non IO blocking
        token_cnt = tokenizer.compute_token_cnt(documents)
        _, _, total_cost = calculate_cost(
            model_name=self.settings.llm_model_name,
            input_token=token_cnt,
            is_batch=True,
        )

        return EmbeddingResponseModel(
            embeding=result_vector,
            token_count=token_cnt,
            total_cost=total_cost,
            duration_ms=duration_ms,
        )


@lru_cache
def get_embedding() -> EmbeddingService:
    _config = {
        "api_key": settings.openai_api_key,
        "model": settings.bi_encoder_model,
        "dimensions": settings.vector_dim,
    }
    return EmbeddingService(
        provider=settings.llm_provider,
        config=_config,
        setting=settings,
        logger=app_logger,
    )
