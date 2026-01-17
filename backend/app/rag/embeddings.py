from functools import lru_cache
from logging import Logger

from langchain_core.embeddings import Embeddings, FakeEmbeddings
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings

from app.core.config import Settings, settings
from app.logger import app_logger

# TODO: replace this with adapter
from app.services.llm.tokenizer import TokenizerService


def get_bi_encoder() -> Embeddings:
    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model=settings.bi_encoder_model,
        dimensions=settings.vector_dim,
    )


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

    def embed_query(self, text: str, tokenizer: TokenizerService) -> list[float]:
        # compute the number of tokens based on the model
        token_cnt = tokenizer.compute_token_cnt(text)
        self.logger.info(f"Total token count: {token_cnt}")
        # get the model name and provider from settings

        # run the logic
        embed = self.client
        return embed.embed_query(text)

    def embed_documents(
        self, documents: list[str], tokenizer: TokenizerService
    ) -> list[float]:
        # compute the number of tokens based on the model
        token_cnt = tokenizer.compute_token_cnt(documents)
        self.logger.info(f"Total token count: {token_cnt}")
        # get the model name and provider from settings

        # run the logic
        embed = self.client
        return embed.embed_documents(documents)


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
