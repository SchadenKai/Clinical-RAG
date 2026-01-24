from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.logger import app_logger
from app.rag.db import VectorClient
from app.routes.dependencies.embedding import get_embedding
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.vector_db import (
    get_vector_client,
    get_vector_client_manual,
)
from app.routes.v1.main import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    app_logger.info("Initializing vector database")
    settings = get_app_settings()
    vector_db = get_vector_client_manual(settings)
    # vector_db.delete_collection()
    vector_db.setup()
    vector_db.load_collection()
    vector_db.smoke_test()

    app_logger.info("Initializing chat model")
    chat_model_service = get_chat_model_service(settings)
    chat_model_service.test_chat_model()

    app_logger.info("Initializing embedding services")
    embedding_service = get_embedding(settings)
    embedding_service.test_client_on_startup()

    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurable via environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {"status_code": 200, "message": "ok"}


@app.get("/health/vector")
def vector_health_check(
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
) -> dict:
    return vector_db.health_check()
