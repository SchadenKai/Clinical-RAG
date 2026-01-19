nebius_model_map = {
    # --- Chat Models (LLMs) ---
    # Llama 3.3
    "meta-llama/Llama-3.3-70B-Instruct": "meta-llama/Llama-3.3-70B-Instruct",
    # Llama 3.1 (Note: Llama 3.1 uses 'Meta-Llama' prefix in HF)
    "meta-llama/Meta-Llama-3.1-405B-Instruct": (
        "meta-llama/Meta-Llama-3.1-405B-Instruct"
    ),
    "meta-llama/Meta-Llama-3.1-70B-Instruct": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-8B-Instruct": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    # Qwen 2.5
    "Qwen/Qwen2.5-72B-Instruct": "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct": "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
    # Qwen 2.5 Coder
    "Qwen/Qwen2.5-Coder-32B-Instruct": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct": "Qwen/Qwen2.5-Coder-7B-Instruct",
    # DeepSeek
    "deepseek-ai/DeepSeek-V3": "deepseek-ai/DeepSeek-V3",
    # Mistral
    "mistralai/Mistral-Large-Instruct-2407": "mistralai/Mistral-Large-Instruct-2407",
    "mistralai/Mistral-Nemo-Instruct-2407": "mistralai/Mistral-Nemo-Instruct-2407",
    "mistralai/Mixtral-8x22B-Instruct-v0.1": "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mistralai/Mixtral-8x7B-Instruct-v0.1": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    # Gemma 2
    "google/gemma-2-27b-it": "google/gemma-2-27b-it",
    "google/gemma-2-9b-it": "google/gemma-2-9b-it",
    # Microsoft Phi
    "microsoft/Phi-3-mini-4k-instruct": "microsoft/Phi-3-mini-4k-instruct",
    # --- Embedding Models ---
    # BGE (BAAI)
    "BAAI/bge-en-icl": "BAAI/bge-en-icl",
    "BAAI/bge-m3": "BAAI/bge-m3",
    "BAAI/bge-multilingual-gemma2": "BAAI/bge-multilingual-gemma2",
    # Qwen Embeddings
    "Qwen/Qwen2.5-Embedding-8B": "Qwen/Qwen2.5-Embedding-8B",  # Validate availability
}
