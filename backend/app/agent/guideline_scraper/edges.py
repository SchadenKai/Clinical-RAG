from typing import Literal

from langgraph.types import Command

from .models import ScraperProgressEnum
from .state import AgentState


def route_entry(
    state: AgentState,
) -> Literal["who_url_collector_node", "cdc_url_collector_node"]:
    """
    Routes the pipeline entry point based on which sources are enabled.
    If WHO scraping is requested, start there (CDC follows sequentially).
    If only CDC is requested, jump directly to the CDC collector.
    """
    if state.scrape_who:
        return "who_url_collector_node"
    return "cdc_url_collector_node"


def is_any_records_found(
    state: AgentState,
) -> Command[Literal["download_and_upload_node", "__end__"]]:
    """
    After merge_records_node: aborts early if no PDF records were collected
    from any source, avoiding a no-op download loop.
    """
    if not state.all_pdf_records:
        return Command(
            goto="__end__",
            update={
                "progress_status": ScraperProgressEnum.DONE,
                "run_metadata": {"error": "No PDF records found from any source"},
            },
        )
    return Command(goto="download_and_upload_node")
