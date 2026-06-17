from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.agent import AgentService


def get_agent_service(db: Annotated[Session, Depends(get_db)]) -> AgentService:
    return AgentService(db)
