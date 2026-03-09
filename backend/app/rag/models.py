from pydantic import BaseModel


class EmbeddingResponseModel(BaseModel):
    embedding: list[float] | list[list[float]]
    sparse_embedding: dict | list[dict] | None = None
    token_count: int
    total_cost: float
    duration_ms: float
    type: str = "embedding"
    event: str = "embedding"
