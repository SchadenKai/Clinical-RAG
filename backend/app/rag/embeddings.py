import time

from langchain_core.embeddings import Embeddings, FakeEmbeddings
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_nebius.embeddings import NebiusEmbeddings
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import Settings, settings
from app.rag.models import EmbeddingResponseModel
from app.services.llm.calculate_cost import calculate_cost

# TODO: replace this with adapter
from app.services.llm.tokenizer import TokenizerService


# TODO: check if this is the best way to import deps
class EmbeddingService:
    def __init__(self, provider, config, setting):
        self._client: Embeddings | None = None
        self.provider: str = provider
        self.config: dict = config
        self.settings: Settings = setting

    @property
    def client(self) -> Embeddings:
        # TODOL Refactor into factory
        if self._client is None:
            if self.provider == "openai":
                self._client = OpenAIEmbeddings(**self.config)
            elif self.provider == "gemini":
                self._client = GoogleGenerativeAIEmbeddings(**self.config)
            elif self.provider == "azure":
                self._client = AzureOpenAIEmbeddings(**self.config)
            # only make this available during development
            elif self.provider == "fake" and settings.dev_mode:
                self._client = FakeEmbeddings(**self.config)
            elif self.provider == "nomic":
                self._client = NomicEmbeddings(**self.config)
            elif self.provider == "nebius":
                self._client = NebiusEmbeddings(**self.config)
            elif self.provider == "openrouter":
                self._client = OpenAIEmbeddings(
                    **self.config, base_url="https://openrouter.ai/api/v1"
                )
            elif self.provider == "huggingface":
                # For HuggingFace, model is passed to model_name argument.
                # Remove it from config first since HuggingFaceEmbeddings doesn't accept "model".
                hf_config = dict(self.config)
                model_n = hf_config.pop("model", None)
                self._client = HuggingFaceEmbeddings(model_name=model_n, **hf_config)
            else:
                self._client = OpenAIEmbeddings(**self.config)
        return self._client

    def test_client_on_startup(self) -> None:
        try:
            self.client.embed_query("")
        except Exception as e:
            raise Exception(f"Something went wrong: {e}") from e

    def embed_query(
        self, text: str, tokenizer: TokenizerService, event_name: str | None = None
    ) -> EmbeddingResponseModel:
        start_time = time.time()
        result_vector = self.client.embed_query(text)
        duration_ms = (time.time() - start_time) * 1000  # convert seconds to ms

        # TODO: Make this non IO blocking
        token_cnt = tokenizer.compute_token_cnt(text, is_embedding_model=True)
        _, _, total_cost = calculate_cost(
            model_name=self.settings.embedding_model,
            input_token=token_cnt,
        )
        return EmbeddingResponseModel(
            embedding=result_vector,
            token_count=token_cnt,
            total_cost=total_cost,
            duration_ms=duration_ms,
            event=event_name,
        )

    def embed_documents(
        self,
        documents: list[str],
        tokenizer: TokenizerService,
        event_name: str | None = None,
    ) -> EmbeddingResponseModel:
        start_time = time.time()
        result_vector = self.client.embed_documents(documents)
        duration_ms = (time.time() - start_time) * 1000  # convert seconds to ms

        # TODO: Make this non IO blocking
        token_cnt = tokenizer.compute_token_cnt(documents, is_embedding_model=True)
        _, _, total_cost = calculate_cost(
            model_name=self.settings.embedding_model,
            input_token=token_cnt,
            is_batch=True,
        )

        return EmbeddingResponseModel(
            embedding=result_vector,
            token_count=token_cnt,
            total_cost=total_cost,
            duration_ms=duration_ms,
            event=event_name,
        )
