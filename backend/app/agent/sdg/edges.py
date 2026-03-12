from typing import Literal

from langgraph.types import Command

from .models import SdgProgressEnum
from .state import AgentState


def is_document_empty(
    state: AgentState,
) -> Command[Literal["document_preparation_node", "__end__"]]:
    if state.raw_document is None:
        return Command(
            goto="__end__",
            update={"progress_status": SdgProgressEnum.DONE},
        )
    return Command(goto="document_preparation_node")
