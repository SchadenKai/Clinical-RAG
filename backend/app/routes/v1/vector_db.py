from typing import Annotated

from fastapi import APIRouter, Depends

from app.rag.db import VectorClient
from app.routes.dependencies.vector_db import get_vector_client

vector_db_router = APIRouter(prefix="/vector_db", tags=["vector_db"])


@vector_db_router.delete("/collection")
def clear_collection(
    vector_service: Annotated[VectorClient, Depends(get_vector_client)],
) -> None:
    vector_cient = vector_service.client
    vector_cient.drop_collection()
    return None
