"""Service layer for chat agent CRUD.

Encapsulates all database access for :class:`~app.models.agent.Agent` behind a
small repository-style interface so routes stay thin and the storage details
stay in one place.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(self) -> list[Agent]:
        stmt = select(Agent).order_by(Agent.created_at.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_agent(self, agent_id: str) -> Agent | None:
        return self.db.get(Agent, agent_id)

    def create_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(
            name=data.name.strip(),
            description=data.description,
            prompt=data.prompt,
            pipeline="general",
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent(self, agent_id: str, data: AgentUpdate) -> Agent | None:
        agent = self.get_agent(agent_id)
        if agent is None:
            return None

        updates = data.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        for field, value in updates.items():
            setattr(agent, field, value)

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: str) -> bool:
        agent = self.get_agent(agent_id)
        if agent is None:
            return False
        self.db.delete(agent)
        self.db.commit()
        return True
