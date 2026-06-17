"""SQLAlchemy model for a chat agent.

A chat agent is a named, described system prompt that a user can select in the
chat page. Most agents run on the general react-agent pipeline using ``prompt``
as the system prompt; the ``pipeline`` discriminator lets a seeded agent (e.g.
``clinical_rag``) route to a specialised pipeline instead. ``pipeline`` is set
by the server, not by the create/update API.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Internal routing discriminator: "general" | "clinical_rag". Not exposed in
    # the create/update schemas — the chat endpoint reads it to pick a pipeline.
    pipeline: Mapped[str] = mapped_column(
        String(32), nullable=False, default="general"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
