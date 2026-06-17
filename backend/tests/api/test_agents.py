"""Tests for the chat agent CRUD service and HTTP routes.

Uses an in-memory SQLite database with the real SQLAlchemy models and a minimal
FastAPI app mounting only the agents router, so the suite stays fast and avoids
the heavy application lifespan (vector DB / LLM startup).
"""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.routes.v1.agents import agents_router
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.agent import AgentService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(agents_router, prefix="/v1")

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAgentService:
    def test_create_strips_name_and_defaults_pipeline(self, db_session: Session):
        # Arrange
        service = AgentService(db_session)

        # Act
        agent = service.create_agent(
            AgentCreate(name="  My Agent  ", description="d", prompt="p")
        )

        # Assert
        assert agent.name == "My Agent"
        assert agent.pipeline == "general"
        assert agent.id

    def test_update_applies_only_provided_fields(self, db_session: Session):
        # Arrange
        service = AgentService(db_session)
        agent = service.create_agent(
            AgentCreate(name="Original", description="desc", prompt="prompt")
        )

        # Act
        updated = service.update_agent(agent.id, AgentUpdate(name="Renamed"))

        # Assert
        assert updated is not None
        assert updated.name == "Renamed"
        assert updated.description == "desc"
        assert updated.prompt == "prompt"

    def test_update_missing_returns_none(self, db_session: Session):
        service = AgentService(db_session)
        assert service.update_agent("missing", AgentUpdate(name="x")) is None

    def test_delete_missing_returns_false(self, db_session: Session):
        service = AgentService(db_session)
        assert service.delete_agent("missing") is False


class TestAgentRoutes:
    def test_list_is_empty_initially(self, client: TestClient):
        response = client.get("/v1/agents")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_returns_201_with_body(self, client: TestClient):
        # Act
        response = client.post(
            "/v1/agents",
            json={"name": "Triage", "description": "Sorts cases", "prompt": "Be terse"},
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Triage"
        assert body["description"] == "Sorts cases"
        assert body["prompt"] == "Be terse"
        assert body["pipeline"] == "general"
        assert body["id"]

    def test_create_rejects_blank_name(self, client: TestClient):
        response = client.post("/v1/agents", json={"name": ""})
        assert response.status_code == 422

    def test_get_roundtrip_and_listing(self, client: TestClient):
        created = client.post("/v1/agents", json={"name": "A"}).json()

        fetched = client.get(f"/v1/agents/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]

        listed = client.get("/v1/agents").json()
        assert len(listed) == 1

    def test_get_missing_returns_404(self, client: TestClient):
        assert client.get("/v1/agents/nope").status_code == 404

    def test_update_changes_fields(self, client: TestClient):
        created = client.post(
            "/v1/agents", json={"name": "Old", "prompt": "p"}
        ).json()

        response = client.put(
            f"/v1/agents/{created['id']}", json={"name": "New"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "New"
        assert body["prompt"] == "p"

    def test_update_missing_returns_404(self, client: TestClient):
        assert client.put("/v1/agents/nope", json={"name": "x"}).status_code == 404

    def test_delete_removes_agent(self, client: TestClient):
        created = client.post("/v1/agents", json={"name": "Temp"}).json()

        deleted = client.delete(f"/v1/agents/{created['id']}")
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "success"

        assert client.get(f"/v1/agents/{created['id']}").status_code == 404

    def test_delete_missing_returns_404(self, client: TestClient):
        assert client.delete("/v1/agents/nope").status_code == 404
