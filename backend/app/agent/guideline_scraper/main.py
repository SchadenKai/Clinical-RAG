from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph

from .edges import is_any_records_found, route_entry
from .nodes import (
    cdc_url_collector_node,
    download_and_upload_node,
    merge_records_node,
    who_url_collector_node,
)
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("who_url_collector_node", who_url_collector_node)
graph.add_node("cdc_url_collector_node", cdc_url_collector_node)
graph.add_node("merge_records_node", merge_records_node)
graph.add_node("is_any_records_found", is_any_records_found)
graph.add_node("download_and_upload_node", download_and_upload_node)

graph.set_finish_point("download_and_upload_node")

graph.add_conditional_edges(START, route_entry)
graph.add_edge("who_url_collector_node", "cdc_url_collector_node")
graph.add_edge("cdc_url_collector_node", "merge_records_node")
graph.add_edge("merge_records_node", "is_any_records_found")

checkpointer = InMemorySaver()

agent = graph.compile(checkpointer=checkpointer)
