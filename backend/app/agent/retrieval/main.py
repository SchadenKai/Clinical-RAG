from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

from .nodes import (
    citation_verification,
    embed_query,
    final_report_generation,
    is_citation_correct,
    is_query_safe,
    refusal_node,
    safety_classifier_node,
    search,
    should_use_llm,
)
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("safety_classifier_node", safety_classifier_node)
graph.add_node("refusal_node", refusal_node)
graph.add_node("embed_query", embed_query)
graph.add_node("search", search)
graph.add_node("final_report_generation", final_report_generation)
graph.add_node("citation_verification", citation_verification)

graph.set_entry_point("safety_classifier_node")
graph.set_finish_point("citation_verification")
graph.set_finish_point("refusal_node")

graph.add_conditional_edges("safety_classifier_node", is_query_safe)
graph.add_edge("embed_query", "search")
graph.add_conditional_edges("search", should_use_llm)
graph.add_edge("final_report_generation", "citation_verification")
graph.add_conditional_edges("citation_verification", is_citation_correct)

checkpointer = InMemorySaver()

agent = graph.compile(checkpointer=checkpointer)
