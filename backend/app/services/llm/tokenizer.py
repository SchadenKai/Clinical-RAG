from functools import lru_cache

import tiktoken

from app.core.config import settings


class TokenizerService:
    def __init__(self, model):
        self.tokenizer_model = None
        self.model: str = model

    def get_tokenizer(self):
        if self.tokenizer_model is not None:
            return self.tokenizer_model

        if self.model.startswith("o") or self.model.startswith("gpt"):
            encoding_name = tiktoken.encoding_name_for_model(self.model)
            self.tokenizer_model = tiktoken.get_encoding(encoding_name)
            return self.tokenizer_model
        elif self.model.startswith("claude"):
            # To be filled up later using claude's tokenizer
            pass
        elif self.model.startswith("gemini"):
            # To be filled up later using gemini's tokenizer
            pass
        else:
            print("[ERROR] The model given is not found")

    def compute_token_cnt(self, text: str | list[str]) -> int | list[int]:
        tokenizer = self.get_tokenizer()
        if isinstance(text, list):
            return [len(tokens) for tokens in tokenizer.encode_batch(text)]
        return len(tokenizer.encode(text))


@lru_cache
def get_tokenizer() -> TokenizerService:
    return TokenizerService(settings.llm_model_name)
