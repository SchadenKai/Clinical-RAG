from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from app.core.config import settings
from app.core.vector import VectorClient, get_vector_client
from app.routes.v1.main import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    vector_db = VectorClient()
    # vector_db.delete_collection()
    vector_db.setup()
    vector_db.load_collection()
    print("[INFO] Getting started")
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
