"""Pydantic schemas for the chat agent CRUD API.

The public contract is intentionally limited to ``name``, ``description`` and
``prompt`` — the fields a user edits. The ``pipeline`` discriminator is server
managed and only surfaced on read responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Upper bounds guard the storage layer and the LLM context window against
# oversized payloads on these unauthenticated endpoints.
_MAX_DESCRIPTION_LEN = 2000
_MAX_PROMPT_LEN = 32000


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=_MAX_DESCRIPTION_LEN)
    prompt: str = Field(default="", max_length=_MAX_PROMPT_LEN)


class AgentCreate(AgentBase):
    """Payload for creating an agent."""


class AgentUpdate(BaseModel):
    """Partial update — only provided fields are applied."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=_MAX_DESCRIPTION_LEN)
    prompt: Optional[str] = Field(default=None, max_length=_MAX_PROMPT_LEN)


class AgentRead(AgentBase):
    id: str
    pipeline: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDeleteResponse(BaseModel):
    status: str = "success"
    message: str
