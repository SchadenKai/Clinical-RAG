from fastapi import APIRouter

from .chat import chat_router
from .rag import rag_router
from .vector_db import vector_db_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(chat_router)
v1_router.include_router(rag_router)
v1_router.include_router(vector_db_router)