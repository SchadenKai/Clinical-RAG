from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.chat.context import AgentContext
from app.agent.chat.edges import (
    route_after_execute,
    route_after_react,
    route_by_mode,
)
from app.agent.chat.nodes import (
    complexity_router,
    execute_node,
    fast_node,
    plan_node,
    react_loop_node,
)
from app.agent.chat.state import AgentState
from app.agent.chat.tools import clinical_retrieval_tool

graph = StateGraph(state_schema=AgentState, config_schema=AgentContext)

graph.add_node("complexity_router", complexity_router)
graph.add_node("fast_node", fast_node)
graph.add_node("react_loop_node", react_loop_node)
graph.add_node("plan_node", plan_node)
graph.add_node("execute_node", execute_node)

tools = [clinical_retrieval_tool]
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "complexity_router")

graph.add_conditional_edges("complexity_router", route_by_mode)

graph.add_edge("fast_node", END)

graph.add_conditional_edges("react_loop_node", route_after_react)
graph.add_edge("tools", "react_loop_node")

graph.add_edge("plan_node", "execute_node")
graph.add_conditional_edges("execute_node", route_after_execute)

checkpointer = InMemorySaver()
agent = graph.compile(checkpointer=checkpointer)
