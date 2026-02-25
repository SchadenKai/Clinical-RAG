import tiktoken
from transformers import AutoTokenizer

from app.core.config import settings
from app.logger import app_logger

from ._tokenizer_list import nebius_model_map


class TokenizerService:
    def __init__(self, model, embedding, model_provider, embedding_provider):
        self._tokenizer_model = None
        self._embedding_tokenizer_model = None
        self.model: str = model
        self.embedding: str = embedding
        self.model_provider: str = model_provider
        self.embedding_provider: str = embedding_provider
        self.fallback_tokenizer: str = "bert-base-uncased"

    @property
    def embedding_tokenizer(self):
        if self._embedding_tokenizer_model is not None:
            return self._embedding_tokenizer_model

        if self.model_provider == "openai":
            encoding_name = tiktoken.encoding_name_for_model(self.embedding)
            self._embedding_tokenizer_model = tiktoken.get_encoding(encoding_name)
        else:
            try:
                hf_model_id = nebius_model_map[self.embedding.replace("-fast", "")]
                self._embedding_tokenizer_model = AutoTokenizer.from_pretrained(
                    hf_model_id, token=settings.hf_api_key, trust_remote_code=True
                )
            except Exception as _:
                app_logger.warning(
                    "Given embedding provider is not yet supported."
                    "Using a fallback tokenizer instead"
                )
                self._embedding_tokenizer_model = AutoTokenizer.from_pretrained(
                    self.fallback_tokenizer,
                    token=settings.hf_api_key,
                    trust_remote_code=True,
                )

        app_logger.info(
            f"Using {self._embedding_tokenizer_model.name} "
            f"tokenizer model for given model: {self.embedding}"
        )
        return self._embedding_tokenizer_model

    @property
    def llm_tokenizer(self):
        if self._tokenizer_model is not None:
            return self._tokenizer_model

        if self.model_provider == "openai":
            encoding_name = tiktoken.encoding_name_for_model(self.model)
            self._tokenizer_model = tiktoken.get_encoding(encoding_name)
            return self._tokenizer_model
        else:
            try:
                hf_model_id = nebius_model_map[self.embedding.replace("-fast", "")]
                self._tokenizer_model = AutoTokenizer.from_pretrained(
                    hf_model_id, token=settings.hf_api_key, trust_remote_code=True
                )
            except Exception as _:
                app_logger.warning(
                    "Given embedding provider is not yet supported."
                    "Using a fallback tokenizer instead"
                )
                self._tokenizer_model = AutoTokenizer.from_pretrained(
                    self.fallback_tokenizer,
                    token=settings.hf_api_key,
                    trust_remote_code=True,
                )

        app_logger.info(
            f"Using {self._tokenizer_model.name} "
            f"tokenizer model for given model: {self.embedding}"
        )
        return self._tokenizer_model

    def compute_token_cnt(
        self, text: str | list[str], is_embedding_model: bool = True
    ) -> int:
        tokenizer = (
            self.embedding_tokenizer if is_embedding_model else self.llm_tokenizer
        )
        if isinstance(text, list):
            try:
                return sum([len(tokens) for tokens in tokenizer.encode_batch(text)])
            except Exception as e:
                app_logger.warning(
                    f"Something went wrong during batch tokenization: {e}"
                )
                tokens = tokenizer(text)
                token_count = sum([len(token) for token in tokens["input_ids"]])
                if tokens is None:
                    app_logger.error("Tokens is missing")
                    raise ValueError("Tokens is missing") from e
                return token_count
        return len(tokenizer.encode(text))
