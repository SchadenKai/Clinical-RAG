from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

from .nodes import embed_query, final_report_generation, search, should_use_llm
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("embed_query", embed_query)
graph.add_node("search", search)
graph.add_node("final_report_generation", final_report_generation)

graph.set_entry_point("embed_query")
graph.set_finish_point("final_report_generation")


graph.add_edge("embed_query", "search")
graph.add_conditional_edges("search", should_use_llm)

checkpointer = InMemorySaver()

agent = graph.compile(checkpointer=checkpointer)
