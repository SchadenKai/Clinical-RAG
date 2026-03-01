from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage

from app.agent.chat.state import AgentState


def route_by_mode(
    state: AgentState,
) -> Literal["fast_node", "react_loop_node", "plan_node"]:
    mode_map = {
        "fast": "fast_node",
        "react": "react_loop_node",
        "plan_and_execute": "plan_node",
    }
    return mode_map.get(state.mode or "fast", "fast_node")


def route_after_react(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Route for managing the flow of ReAct LLM Flow
    """
    messages = state.messages
    last_message: BaseMessage = messages[-1]

    if (
        isinstance(last_message, AIMessage)
        and hasattr(last_message, "tool_calls")
        and last_message.tool_calls
    ):
        return "tools"

    return "__end__"


def route_after_execute(state: AgentState) -> Literal["execute_node", "__end__"]:
    """
    Route for managing the flow of Plan-and-Execute LLM Flow
    """
    plan = state.plan or []
    completed = state.completed_steps or []
    if len(completed) >= len(plan):
        return "__end__"
    return "execute_node"
