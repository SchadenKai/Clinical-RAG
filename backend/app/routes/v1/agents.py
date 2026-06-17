"""CRUD endpoints for chat agents.

Agents are platform-wide records (no per-user ownership). Built-in agents are
seeded by the initial migration and are editable/deletable like any other.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.agent import Agent
from app.routes.dependencies.agent_service import get_agent_service
from app.schemas.agent import (
    AgentCreate,
    AgentDeleteResponse,
    AgentRead,
    AgentUpdate,
)
from app.services.agent import AgentService

agents_router = APIRouter(prefix="/agents", tags=["agents"])

# Routes return ORM ``Agent`` objects; FastAPI serialises them through the
# declared ``response_model`` (the ``AgentRead`` schema).


@agents_router.get("", response_model=list[AgentRead])
def list_agents(
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> list[Agent]:
    return agent_service.list_agents()


@agents_router.get("/{agent_id}", response_model=AgentRead)
def get_agent(
    agent_id: str,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> Agent:
    agent = agent_service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return agent


@agents_router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(
    data: AgentCreate,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> Agent:
    return agent_service.create_agent(data)


@agents_router.put("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: str,
    data: AgentUpdate,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> Agent:
    agent = agent_service.update_agent(agent_id, data)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return agent


@agents_router.delete("/{agent_id}", response_model=AgentDeleteResponse)
def delete_agent(
    agent_id: str,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentDeleteResponse:
    deleted = agent_service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return AgentDeleteResponse(message=f"Agent '{agent_id}' deleted")
