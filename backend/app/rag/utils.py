from app.logger import app_logger
from app.rag.constants import EMBEDDING_CTX_LIMITS


def get_chunk_settings(model_name: str) -> dict[int, int]:
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
        return chunk_size
    ctx_limit = EMBEDDING_CTX_LIMITS[model_name]
    for size in chunk_size_values:
        if ctx_limit > size:
            continue
        chunk_size = size

    chunk_overlap = round(chunk_size * chunk_overlap_percentage)
    chunk_overlap = chunk_overlap if chunk_overlap <= 50 else 50

    return {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
