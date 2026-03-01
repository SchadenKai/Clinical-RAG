import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from app.agent.chat.context import AgentContext
from app.agent.chat.state import AgentState
from app.logger import app_logger


def complexity_router(
    state: AgentState, runtime: Runtime[AgentContext]
) -> dict[str, Any]:
    """
    Decides the mode of execution based on the query complexity.
    Modes: 'fast', 'react', 'plan_and_execute'
    """
    context = runtime.context
    messages = state.messages
    last_user_message = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)), None
    )

    if not last_user_message:
        return {"mode": "fast"}

    query = last_user_message.content.lower()

    if "plan" in query or "step by step" in query or "complex" in query:
        mode = "plan_and_execute"
    elif context.tools:
        mode = "react"
    else:
        mode = "fast"

    app_logger.info(f"Routing query to mode: {mode}")
    return {"mode": mode}


def fast_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict[str, Any]:
    """
    Fast direct text generation using the LLM without tools.
    """
    response = runtime.context.llm.invoke(state.messages)
    return {"messages": [response]}


def react_loop_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> dict[str, Any]:
    """
    LLM call for the ReAct flow.
    """
    context = runtime.context
    llm_with_tools = context.llm.bind_tools(context.tools)
    response = llm_with_tools.invoke(state.messages)
    return {"messages": [response]}


def plan_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict[str, Any]:
    """
    Generates a step-by-step plan.
    """
    messages = list(state.messages)
    messages.append(
        HumanMessage(
            content=(
                "Please provide a step-by-step plan to resolve my request. "
                "Format it as a JSON array of strings `['step 1', 'step 2']`."
            )
        )
    )

    response = runtime.context.llm.invoke(messages)

    plan = []
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        plan = json.loads(content)
        if not isinstance(plan, list):
            plan = []
    except Exception as e:
        app_logger.warning(f"Failed to parse plan JSON: {e}")
        plan = [response.content]

    return {"plan": plan, "completed_steps": []}


def execute_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict[str, Any]:
    """
    Executes the plan steps using the React approach.
    """
    context = runtime.context
    plan = state.plan or []
    completed = state.completed_steps or []

    if len(completed) >= len(plan):
        return {}

    current_step = plan[len(completed)]

    sub_messages = list(state.messages) + [
        SystemMessage(
            content=f"You are executing a plan step: {current_step}. "
            "Use your tools if necessary."
        )
    ]

    llm_with_tools = context.llm.bind_tools(context.tools)
    response = llm_with_tools.invoke(sub_messages)

    completed = list(completed) + [current_step]

    return {
        "messages": [response],
        "completed_steps": completed,
    }
