from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

from .nodes import (
    citation_verification,
    embed_query,
    final_report_generation,
    generate_queries,
    is_citation_correct,
    is_query_safe,
    judge_decision,
    llm_judge_node,
    refusal_node,
    rerank_node,
    safety_classifier_node,
    search,
    should_use_llm,
)
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("safety_classifier_node", safety_classifier_node)
graph.add_node("refusal_node", refusal_node)
graph.add_node("generate_queries", generate_queries)
graph.add_node("embed_query", embed_query)
graph.add_node("search", search)
graph.add_node("rerank_node", rerank_node)
graph.add_node("final_report_generation", final_report_generation)
graph.add_node("citation_verification", citation_verification)
graph.add_node("llm_judge_node", llm_judge_node)

graph.set_entry_point("safety_classifier_node")
graph.set_finish_point("refusal_node")

graph.add_conditional_edges("safety_classifier_node", is_query_safe)
graph.add_edge("generate_queries", "embed_query")
graph.add_edge("embed_query", "search")
graph.add_edge("search", "rerank_node")
graph.add_conditional_edges("rerank_node", should_use_llm)
graph.add_edge("final_report_generation", "citation_verification")
graph.add_conditional_edges("citation_verification", is_citation_correct)
graph.add_conditional_edges("llm_judge_node", judge_decision)

checkpointer = InMemorySaver()

agent = graph.compile(checkpointer=checkpointer)
