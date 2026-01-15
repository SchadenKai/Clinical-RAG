from .state import AgentState
from langgraph.runtime import Runtime
from .context import AgentContext
from langchain_core.messages import HumanMessage


def validate_input_node(state: AgentState) -> AgentState:
    if not isinstance(state.messages[-1], HumanMessage):
        print("[ERROR] HumanMessage is expected at the end of the input message list")

    return state


def call_llm_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    llm = runtime.context.llm

    if not isinstance(state.messages[-1], HumanMessage):
        return state

    response = llm.invoke(state.messages)

    return AgentState(messages=[response])
