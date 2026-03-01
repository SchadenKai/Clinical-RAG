from fastapi import APIRouter

from app.routes.v1.auth import router as auth_router
from app.routes.v1.catalog import catalog_router
from app.routes.v1.chat import chat_router
from app.routes.v1.indexing import indexing_router
from app.routes.v1.rag import rag_router
from app.routes.v1.settings import settings_router
from app.routes.v1.users import router as users_router
from app.routes.v1.vector_db import vector_db_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(chat_router)
v1_router.include_router(rag_router)
v1_router.include_router(vector_db_router)
v1_router.include_router(indexing_router)
v1_router.include_router(catalog_router)
v1_router.include_router(settings_router)
v1_router.include_router(users_router, prefix="/users", tags=["users"])
v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
