from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph

from .edges import is_document_empty
from .nodes import (
    document_preparation_node,
    file_ingestion_node,
    knowledge_graph_node,
    store_goldens_node,
    testset_generation_node,
)
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("file_ingestion_node", file_ingestion_node)
graph.add_node("is_document_empty", is_document_empty)
graph.add_node("document_preparation_node", document_preparation_node)
graph.add_node("knowledge_graph_node", knowledge_graph_node)
graph.add_node("testset_generation_node", testset_generation_node)
graph.add_node("store_goldens_node", store_goldens_node)

graph.set_finish_point("store_goldens_node")

graph.add_edge(START, "file_ingestion_node")
graph.add_edge("file_ingestion_node", "is_document_empty")
graph.add_edge("document_preparation_node", "knowledge_graph_node")
graph.add_edge("knowledge_graph_node", "testset_generation_node")
graph.add_edge("testset_generation_node", "store_goldens_node")

checkpointer = InMemorySaver()
agent = graph.compile(checkpointer=checkpointer)
