model_pricing = {
    # =========================================================================
    # OPENAI LLMs
    # Policy: Batch API is 50% cheaper than standard (Input & Output).
    # =========================================================================
    "gpt-4-0125-preview": {
        "input_price": 10.00,
        "output_price": 30.00,
        "batch_input_price": 5.00,
        "batch_output_price": 15.00,
    },
    "gpt-4-turbo-preview": {
        "input_price": 10.00,
        "output_price": 30.00,
        "batch_input_price": 5.00,
        "batch_output_price": 15.00,
    },
    "gpt-4-1106-preview": {
        "input_price": 10.00,
        "output_price": 30.00,
        "batch_input_price": 5.00,
        "batch_output_price": 15.00,
    },
    "gpt-4-1106-vision-preview": {
        "input_price": 10.00,
        "output_price": 30.00,
        "batch_input_price": 5.00,
        "batch_output_price": 15.00,
    },
    "gpt-4": {
        "input_price": 30.00,
        "output_price": 60.00,
        "batch_input_price": 15.00,
        "batch_output_price": 30.00,
    },
    "gpt-4-32k": {
        "input_price": 60.00,
        "output_price": 120.00,
        "batch_input_price": 30.00,
        "batch_output_price": 60.00,
    },
    "gpt-4o-mini": {
        "input_price": 0.15,
        "output_price": 0.60,
        "batch_input_price": 0.075,
        "batch_output_price": 0.30,
    },
    "gpt-4o": {
        "input_price": 2.50,
        "output_price": 10.00,
        "batch_input_price": 1.25,
        "batch_output_price": 5.00,
    },
    "gpt-4o-2024-08-06": {
        "input_price": 2.50,
        "output_price": 10.00,
        "batch_input_price": 1.25,
        "batch_output_price": 5.00,
    },
    "gpt-4o-mini-2024-07-18": {
        "input_price": 0.15,
        "output_price": 0.60,
        "batch_input_price": 0.075,
        "batch_output_price": 0.30,
    },
    "gpt-4.1-mini-2025-04-14": {
        "input_price": 0.40,
        "output_price": 1.60,
        "batch_input_price": 0.20,
        "batch_output_price": 0.80,
    },
    "gpt-4.1-mini": {
        "input_price": 0.40,
        "output_price": 1.60,
        "batch_input_price": 0.20,
        "batch_output_price": 0.80,
    },
    "gpt-5-mini": {
        "input_price": 0.25,
        "output_price": 2.00,
        "batch_input_price": 0.125,
        "batch_output_price": 1.00,
    },
    "gpt-5": {
        "input_price": 1.25,
        "output_price": 10.00,
        "batch_input_price": 0.625,
        "batch_output_price": 5.00,
    },
    "gpt-5-mini-2025-08-07": {
        "input_price": 0.25,
        "output_price": 2.00,
        "batch_input_price": 0.125,
        "batch_output_price": 1.00,
    },
    "o3-mini-2025-01-31": {
        "input_price": 1.10,
        "output_price": 4.40,
        "batch_input_price": 0.55,
        "batch_output_price": 2.20,
    },
    "ft:gpt-4o-mini-2024-07-18": {
        "input_price": 0.30,
        "output_price": 1.20,
        "batch_input_price": 0.15,
        "batch_output_price": 0.60,
    },
    "gpt-3.5-turbo-0125": {
        "input_price": 0.50,
        "output_price": 1.50,
        "batch_input_price": 0.25,
        "batch_output_price": 0.75,
    },
    "gpt-3.5-turbo": {
        "input_price": 0.50,
        "output_price": 1.50,
        "batch_input_price": 0.25,
        "batch_output_price": 0.75,
    },
    "gpt-3.5-turbo-instruct": {
        "input_price": 1.50,
        "output_price": 2.00,
        "batch_input_price": 0.75,
        "batch_output_price": 1.00,
    },
    "gpt-3.5-turbo-1106": {
        "input_price": 1.00,
        "output_price": 2.00,
        "batch_input_price": 0.50,
        "batch_output_price": 1.00,
    },
    "gpt-3.5-turbo-0613": {
        "input_price": 1.50,
        "output_price": 2.00,
        "batch_input_price": 0.75,
        "batch_output_price": 1.00,
    },
    "gpt-3.5-turbo-16k-0613": {
        "input_price": 3.00,
        "output_price": 4.00,
        "batch_input_price": 1.50,
        "batch_output_price": 2.00,
    },
    "gpt-3.5-turbo-0301": {
        "input_price": 1.50,
        "output_price": 2.00,
        "batch_input_price": 0.75,
        "batch_output_price": 1.00,
    },
    # --- OpenAI Embeddings ---
    "text-embedding-3-small": {
        "input_price": 0.02,
        "output_price": 0.00,
        "batch_input_price": 0.01,
        "batch_output_price": 0.00,
    },
    "text-embedding-3-large": {
        "input_price": 0.13,
        "output_price": 0.00,
        "batch_input_price": 0.065,
        "batch_output_price": 0.00,
    },
    "text-embedding-ada-002": {
        "input_price": 0.10,
        "output_price": 0.00,
        "batch_input_price": 0.05,
        "batch_output_price": 0.00,
    },
    # =========================================================================
    # ANTHROPIC LLMs
    # Policy: Message Batches API is 50% cheaper than standard.
    # =========================================================================
    "claude-3-haiku-20240307-v1": {
        "input_price": 0.25,
        "output_price": 1.25,
        "batch_input_price": 0.125,
        "batch_output_price": 0.625,
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input_price": 0.25,
        "output_price": 1.25,
        "batch_input_price": 0.125,
        "batch_output_price": 0.625,
    },
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": {
        "input_price": 1.00,
        "output_price": 5.00,
        "batch_input_price": 0.50,
        "batch_output_price": 2.50,
    },
    "claude-3-5-sonnet-20240620-v1": {
        "input_price": 3.00,
        "output_price": 15.00,
        "batch_input_price": 1.50,
        "batch_output_price": 7.50,
    },
    "claude-3-7-sonnet-20250219": {
        "input_price": 3.00,
        "output_price": 15.00,
        "batch_input_price": 1.50,
        "batch_output_price": 7.50,
    },
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "input_price": 3.00,
        "output_price": 15.00,
        "batch_input_price": 1.50,
        "batch_output_price": 7.50,
    },
    # =========================================================================
    # GOOGLE GEMINI
    # Note: Vertex AI Batch Prediction often uses node-hour billing, not per-token.
    # Batch pricing is marked as None to avoid inaccurate estimates.
    # =========================================================================
    "gemini-1.5-flash-preview-0514": {
        "input_price": 0.50,
        "output_price": 1.50,
        "batch_input_price": None,
        "batch_output_price": None,
    },
    "text-embedding-004": {
        "input_price": 0.10,
        "output_price": 0.00,
        "batch_input_price": None,
        "batch_output_price": None,
    },
    # =========================================================================
    # META (Direct/Generic)
    # =========================================================================
    "meta.llama3-8b-instruct-v1": {
        "input_price": 0.40,
        "output_price": 0.60,
        "batch_input_price": None,
        "batch_output_price": None,
    },
    "meta.llama3-1-70b-instruct-v1:0": {
        "input_price": 2.65,
        "output_price": 3.50,
        "batch_input_price": None,
        "batch_output_price": None,
    },
    "meta.llama3-1-8b-instruct-v1:0": {
        "input_price": 0.30,
        "output_price": 0.60,
        "batch_input_price": None,
        "batch_output_price": None,
    },
    # =========================================================================
    # NEBIUS AI MODELS
    # Policy: Batch inference is automatically 50% off the Base price.
    # =========================================================================
    # --- DeepSeek ---
    "deepseek-ai/DeepSeek-V3": {
        "input_price": 0.50,
        "output_price": 1.50,
        "batch_input_price": 0.25,
        "batch_output_price": 0.75,
    },
    "deepseek-ai/DeepSeek-R1": {
        "input_price": 0.80,
        "output_price": 2.40,
        "batch_input_price": 0.40,
        "batch_output_price": 1.20,
    },
    # --- Meta Llama ---
    "meta-llama/Meta-Llama-3.1-405B-Instruct": {
        "input_price": 1.00,
        "output_price": 3.00,
        "batch_input_price": 0.50,
        "batch_output_price": 1.50,
    },
    "meta-llama/Meta-Llama-3.1-70B-Instruct": {
        "input_price": 0.13,
        "output_price": 0.40,
        "batch_input_price": 0.065,
        "batch_output_price": 0.20,
    },
    "meta-llama/Meta-Llama-3.1-8B-Instruct": {
        "input_price": 0.02,
        "output_price": 0.06,
        "batch_input_price": 0.01,
        "batch_output_price": 0.03,
    },
    "meta-llama/Llama-3.3-70B-Instruct": {
        "input_price": 0.13,
        "output_price": 0.40,
        "batch_input_price": 0.065,
        "batch_output_price": 0.20,
    },
    "meta-llama/Llama-3.2-90B-Vision-Instruct": {
        "input_price": 0.13,
        "output_price": 0.40,
        "batch_input_price": 0.065,
        "batch_output_price": 0.20,
    },
    "meta-llama/Llama-3.2-11B-Vision-Instruct": {
        "input_price": 0.03,
        "output_price": 0.09,
        "batch_input_price": 0.015,
        "batch_output_price": 0.045,
    },
    # --- Qwen ---
    "Qwen/Qwen2.5-72B-Instruct": {
        "input_price": 0.13,
        "output_price": 0.40,
        "batch_input_price": 0.065,
        "batch_output_price": 0.20,
    },
    "Qwen/Qwen2.5-32B-Instruct": {
        "input_price": 0.06,
        "output_price": 0.20,
        "batch_input_price": 0.03,
        "batch_output_price": 0.10,
    },
    "Qwen/Qwen2.5-Coder-32B-Instruct": {
        "input_price": 0.06,
        "output_price": 0.20,
        "batch_input_price": 0.03,
        "batch_output_price": 0.10,
    },
    "Qwen/Qwen2.5-Coder-7B-Instruct": {
        "input_price": 0.03,
        "output_price": 0.09,
        "batch_input_price": 0.015,
        "batch_output_price": 0.045,
    },
    "Qwen/Qwen-2-VL-72B-Instruct": {
        "input_price": 0.13,
        "output_price": 0.40,
        "batch_input_price": 0.065,
        "batch_output_price": 0.20,
    },
    "Qwen/Qwen3-235B-A22B-Instruct-2507": {
        "input_price": 0.2,
        "output_price": 0.60,
        "batch_input_price": 0.2,
        "batch_output_price": 0.60,
    },
    # --- Other Nebius ---
    "mistralai/Mistral-Nemo-Instruct-2407": {
        "input_price": 0.08,
        "output_price": 0.24,
        "batch_input_price": 0.04,
        "batch_output_price": 0.12,
    },
    "openai/gpt-oss-120b": {
        "input_price": 0.15,
        "output_price": 0.60,
        "batch_input_price": 0.15,
        "batch_output_price": 0.60,
    },
    "meta-llama/Llama-3.3-70B-Instruct-fast": {
        "input_price": 0.25,
        "output_price": 0.75,
        "batch_input_price": 0.25,
        "batch_output_price": 0.75,
    },
    "google/gemma-2-9b-it": {
        "input_price": 0.03,
        "output_price": 0.09,
        "batch_input_price": 0.015,
        "batch_output_price": 0.045,
    },
    "google/gemma-2-27b-it": {
        "input_price": 0.27,
        "output_price": 0.27,
        "batch_input_price": 0.135,
        "batch_output_price": 0.135,
    },
    "baai/bge-multilingual-gemma2": {
        "input_price": 0.01,
        "output_price": 0.00,
        "batch_input_price": 0.01,
        "batch_output_price": 0.00,
    },
    "MiniMaxAI/MiniMax-M2.1": {
        "input_price": 0.30,
        "output_price": 1.20,
        "batch_input_price": 0.00,
        "batch_output_price": 0.00,
    },
    "microsoft/Phi-3.5-mini-instruct": {
        "input_price": 0.02,
        "output_price": 0.06,
        "batch_input_price": 0.01,
        "batch_output_price": 0.03,
    },
    # --- Nebius Embeddings ---
    "Qwen/Qwen3-Embedding-8B": {
        "input_price": 0.01,
        "output_price": 0.00,
        "batch_input_price": 0.005,
        "batch_output_price": 0.00,
    },
}
