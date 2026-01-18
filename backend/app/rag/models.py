from pydantic import BaseModel


class EmbeddingResponseModel(BaseModel):
    embeding: list[float] | list[list[float]]
    token_count: int
    total_cost: float
    duration_ms: float
    type: str = "embedding"
    event: str = "embedding"
