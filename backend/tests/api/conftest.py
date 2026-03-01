"""
Shared pytest fixtures for API integration tests.

Uses FastAPI's TestClient with an in-memory SQLite database.
Creates a stripped-down test app (no lifespan/startup hooks) to avoid
needing a running Milvus, MinIO, or GPU during unit/API tests.
"""

import uuid as _uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest

# ── Patch postgresql.UUID → String BEFORE importing any models ─────────────────
import sqlalchemy.dialects.postgresql as _pg
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import String, create_engine
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import sessionmaker


class _UUIDAsString(TypeDecorator):
    """postgresql.UUID stand-in that works on SQLite."""

    impl = String
    cache_ok = True

    def __init__(self, as_uuid=False, **kwargs):
        self.as_uuid = as_uuid
        kwargs.pop("length", None)
        super().__init__(length=36, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.as_uuid:
            return _uuid.UUID(value)
        return value

_pg.UUID = _UUIDAsString  # type: ignore[attr-defined]

# ── Safe to import now ─────────────────────────────────────────────────────────
from app.core.database import Base  # noqa: E402
from app.db.models import Agent, EmbeddingConfig, LLMConfig, User  # noqa: E402
from app.routes.dependencies.auth import get_current_user  # noqa: E402
from app.routes.dependencies.chat_service import get_chat_service  # noqa: E402
from app.routes.dependencies.db_session import get_db  # noqa: E402
from app.routes.dependencies.file_store import get_s3_service  # noqa: E402
from app.routes.dependencies.rag import (  # noqa: E402
    get_indexing_service,
    get_retrieval_service,
)
from app.routes.dependencies.settings import get_app_settings  # noqa: E402
from app.routes.dependencies.settings_service import get_settings_service  # noqa: E402
from app.routes.dependencies.vector_db import get_vector_client  # noqa: E402
from app.routes.v1.main import v1_router  # noqa: E402

# ── In-Memory SQLite Engine ────────────────────────────────────────────────────

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_api.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Constants ──────────────────────────────────────────────────────────────────

_DEV_USER_ID = str(_uuid.UUID("00000000-0000-0000-0000-000000000001"))


# ── Create tables and seed data ────────────────────────────────────────────────

def _create_tables_and_seed():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    if not db.query(User).filter_by(id=_DEV_USER_ID).first():
        db.add(User(
            id=_DEV_USER_ID, 
            email="test@example.com", 
            name="Test User", 
            hashed_password="hashed_password",
            role="admin"
        ))

    if not db.query(Agent).filter_by(id="general").first():
        db.add(Agent(id="general", name="General Chat", tools=[]))

    if not db.query(Agent).filter_by(id="clinical_rag").first():
        db.add(Agent(id="clinical_rag", name="Clinical RAG", tools=["retrieval_tool"]))

    if not db.query(LLMConfig).first():
        db.add(
            LLMConfig(
                provider="openai",
                model_name="gpt-4o",
                api_key="test-key",
                is_active=True,
            )
        )

    if not db.query(EmbeddingConfig).first():
        db.add(
            EmbeddingConfig(
                provider="openai",
                model_name="text-embedding-3-small",
                api_key="test-key",
                is_active=True,
            )
        )

    db.commit()
    db.close()


_create_tables_and_seed()


# ── Fake dependency implementations ───────────────────────────────────────────

from fastapi import Depends  # noqa: E402


def _fake_current_user(db=Depends(get_db)):  # noqa: B008
    user = db.query(User).filter_by(id=_DEV_USER_ID).first()
    return user


def _fake_s3_service():
    s3 = MagicMock()
    s3.client.generate_presigned_url.return_value = "https://presigned.example.com/file.pdf"
    return s3


def _fake_vector_client():
    return MagicMock()


from app.core.config import settings as _real_settings  # noqa: E402


def _fake_get_app_settings():
    return _real_settings


# ── Minimal test app (NO lifespan — avoids Milvus / GPU on startup) ─────────────


@asynccontextmanager
async def _noop_lifespan(_: FastAPI) -> AsyncGenerator:
    yield


test_app = FastAPI(title="Test App", lifespan=_noop_lifespan)
test_app.include_router(v1_router)

def _fake_chat_service():
    """Mocked ChatService — no real LLM/Milvus connections."""
    from app.db.chat import ChatRepository
    from app.services.chat import ChatService

    _db = TestingSessionLocal()
    return ChatService(
        chat_repository=ChatRepository(_db),
        chat_agent=MagicMock(),
        retrieval_service=MagicMock(),
        chat_model_service=MagicMock(client=MagicMock()),
        settings=_real_settings,
    )


def _fake_retrieval_service():
    """Mocked RetrievalService — no embedding model or vector DB."""
    return MagicMock()


def _fake_indexing_service():
    """Mocked IndexingService — no embedding model or S3."""
    svc = MagicMock()
    svc.upload_file.return_value = None
    svc.ingest_document.return_value = {}
    return svc


def _fake_settings_service():
    """Mocked SettingsService — uses real DB session but avoids external calls."""
    from app.services.settings_service import SettingsService
    db = TestingSessionLocal()
    return SettingsService(db=db)


# Apply dependency overrides
test_app.dependency_overrides[get_db] = override_get_db
test_app.dependency_overrides[get_current_user] = _fake_current_user
test_app.dependency_overrides[get_s3_service] = _fake_s3_service
test_app.dependency_overrides[get_vector_client] = _fake_vector_client
test_app.dependency_overrides[get_app_settings] = _fake_get_app_settings
test_app.dependency_overrides[get_chat_service] = _fake_chat_service
test_app.dependency_overrides[get_retrieval_service] = _fake_retrieval_service
test_app.dependency_overrides[get_indexing_service] = _fake_indexing_service
test_app.dependency_overrides[get_settings_service] = _fake_settings_service


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(test_app) as c:
        yield c


@pytest.fixture()
def db():
    """Fresh DB session per test (function scope)."""
    _db = TestingSessionLocal()
    try:
        yield _db
    finally:
        _db.close()
