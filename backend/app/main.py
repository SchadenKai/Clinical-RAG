from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Getting started")
    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict:
    return {"status_code": 200, "message": "ok"}
