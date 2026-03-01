from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from app.agent.chat.main import agent


@lru_cache
def get_chat_agent() -> CompiledStateGraph:
    return agent
