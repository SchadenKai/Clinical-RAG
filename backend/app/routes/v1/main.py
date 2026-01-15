from fastapi import APIRouter

from .chat import chat_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(chat_router)
