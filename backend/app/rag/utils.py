from app.logger import app_logger
from app.rag.constants import EMBEDDING_CTX_LIMITS


def get_chunk_settings(model_name: str) -> dict[str, int]:
    """
    Get proper chunk size based on the embedding model being used
    """
    chunk_size_values = [128, 512, 1024]
    chunk_overlap_percentage = 0.2
    chunk_size = chunk_size_values[0]

    if model_name not in EMBEDDING_CTX_LIMITS.keys():
        app_logger.warning(
            "Embedding model being used is not recognized. "
            "Falling back to smallest chunk size value."
        )
        chunk_overlap = round(chunk_size * chunk_overlap_percentage)
        chunk_overlap = chunk_overlap if chunk_overlap <= 50 else 50
        return {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

    ctx_limit = EMBEDDING_CTX_LIMITS[model_name]
    
    # If limit is very small (<= 256), use 128
    if ctx_limit <= 256:
        chunk_size = 128
    # If limit is medium (<= 1024), use 512
    elif ctx_limit <= 1024:
        chunk_size = 512
    # Otherwise use 1024
    else:
        chunk_size = 1024

    chunk_overlap = round(chunk_size * chunk_overlap_percentage)
    chunk_overlap = chunk_overlap if chunk_overlap <= 50 else 50

    return {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
