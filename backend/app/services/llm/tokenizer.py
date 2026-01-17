import tiktoken


class Tokenizer:
    def __init__(self):
        self.tokenizer_model = None

    def get_tokenizer_from_model(self, model: str):
        if self.tokenizer_model is not None:
            return self.tokenizer_model

        if model.startswith("o") or model.startswith("gpt"):
            encoding_name = tiktoken.encoding_name_for_model(model)
            self.tokenizer_model = tiktoken.encoding_for_model(encoding_name)
            return self.tokenizer_model
        elif model.startswith("claude"):
            # To be filled up later using claude's tokenizer
            pass
        elif model.startswith("gemini"):
            # To be filled up later using gemini's tokenizer
            pass
        else:
            print("[ERROR] The model given is not found")

    def compute_token_cnt(self, text: str, model_name: str) -> int:
        tokenizer = self.get_tokenizer_from_model(model=model_name)
        return len(tokenizer.encode(text))
