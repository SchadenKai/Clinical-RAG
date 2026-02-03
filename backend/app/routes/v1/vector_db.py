from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.rag.db import VectorClient
from app.routes.dependencies.vector_db import get_vector_client

vector_db_router = APIRouter(prefix="/vector_db", tags=["vector_db"])


@vector_db_router.delete("/collection")
def clear_collection(
    vector_service: Annotated[VectorClient, Depends(get_vector_client)],
) -> None:
    vector_cient = vector_service.client
    try:
        vector_cient.use_database(settings.milvus_db_name)
        vector_cient.drop_collection(settings.milvus_collection_name)
        vector_service.setup()
        vector_service.load_collection()
    except Exception as e:
        raise RuntimeError(f"Something went wrong during deletion: {e}") from e
    return None
