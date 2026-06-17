from fastapi import APIRouter

from .agents import agents_router
from .chat import chat_router
from .messaging import messaging_router
from .rag import rag_router
from .vector_db import vector_db_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(chat_router)
v1_router.include_router(agents_router)
v1_router.include_router(messaging_router)
v1_router.include_router(rag_router)
v1_router.include_router(vector_db_router)
