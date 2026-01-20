from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from app.core.config import settings
from app.logger import app_logger
from app.rag.db import VectorClient, get_vector_client
from app.rag.embeddings import get_embedding
from app.routes.v1.main import v1_router
from app.services.llm.factory import get_chat_model_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    app_logger.info("Initializing vector database")
    vector_db = get_vector_client()
    # vector_db.delete_collection()
    vector_db.setup()
    vector_db.load_collection()
    vector_db.smoke_test()

    app_logger.info("Initializing chat model")
    chat_model_service = get_chat_model_service()
    chat_model_service.test_chat_model()

    app_logger.info("Initializing embedding services")
    embedding_service = get_embedding()
    embedding_service.test_client_on_startup()

    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(v1_router)


@app.get("/health")
def health_check() -> dict:
    return {"status_code": 200, "message": "ok"}


@app.get("/health/vector")
def vector_health_check(
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
) -> dict:
    return vector_db.health_check()
