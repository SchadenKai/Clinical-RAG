# create agent state schema
# create agent object
# create nodes
# routing function if necessary
from langgraph.graph import StateGraph
from .state import AgentState
from .nodes import call_llm_node, validate_input_node

graph = StateGraph(state_schema=AgentState)

graph.add_node("validate_input_node", validate_input_node)
graph.add_node("call_llm_node", call_llm_node)

graph.set_entry_point("validate_input_node")
graph.set_finish_point("call_llm_node")
graph.add_edge("validate_input_node", "call_llm_node")

agent = graph.compile()
