# create agent state schema
# create agent object
# create nodes
# routing function if necessary
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

from .nodes import call_llm_node, validate_input_node
from .state import AgentState

graph = StateGraph(state_schema=AgentState)

graph.add_node("validate_input_node", validate_input_node)
graph.add_node("call_llm_node", call_llm_node)

graph.set_entry_point("validate_input_node")
graph.set_finish_point("call_llm_node")
graph.add_edge("validate_input_node", "call_llm_node")

checkpointer = InMemorySaver()

agent = graph.compile(checkpointer=checkpointer)
