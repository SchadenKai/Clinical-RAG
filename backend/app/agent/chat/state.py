from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel


class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    mode: str | None = None  # fast, react, plan_and_execute
    plan: list[str] | None = None  # Used in plan & execute mode
    completed_steps: list[str] | None = None  # Used in plan & execute mode
