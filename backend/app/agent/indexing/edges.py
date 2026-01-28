from typing import Literal

from langgraph.types import Command

from .models import ProgressStatusEnum
from .state import AgentState


def is_file(
    state: AgentState,
) -> Literal["file_ingestion_node", "web_scrapper"]:
    if state.file_key:
        return "file_ingestion_node"
    return "web_scrapper"


def is_chunked_docs_empty(
    state: AgentState,
) -> Command[Literal["doc_builder_node", "__end__"]]:
    if state.chunked_documents is None or state.chunked_documents == []:
        return Command(
            goto="__end__",
            update=state.model_copy(
                update={"progress_status": ProgressStatusEnum.DONE}
            ),
        )
    return Command(goto="doc_builder_node")
