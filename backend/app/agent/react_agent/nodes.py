from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from app.agent.streaming import stream_chat_response

from .context import AgentContext
from .state import AgentState


def validate_input_node(state: AgentState) -> AgentState:
    if not isinstance(state.messages[-1], HumanMessage):
        print("[ERROR] HumanMessage is expected at the end of the input message list")

    return state


def call_llm_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    llm = runtime.context.llm

    if not isinstance(state.messages[-1], HumanMessage):
        return state

    # Stream so LangGraph's ``messages`` mode emits token-by-token deltas.
    response = stream_chat_response(llm, state.messages)

    return AgentState(messages=[response])
