from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.routes.v1.main import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
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
