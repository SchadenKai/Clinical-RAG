"""Helpers for streaming chat-model responses inside LangGraph nodes.

Calling ``.stream()`` (instead of ``.invoke()``) inside a node is what makes
LangGraph's ``messages`` stream mode emit real, token-by-token deltas. The
AG-UI layer forwards those deltas to the frontend as ``TEXT_MESSAGE_CONTENT``
chunks, giving the user a live, streaming response.
"""

from collections.abc import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage


def stream_chat_response(
    llm: BaseChatModel, messages: Sequence[BaseMessage]
) -> BaseMessage:
    """Stream ``llm`` over ``messages`` and return the accumulated message.

    The streaming call produces the per-token chunks that LangGraph surfaces in
    ``messages`` mode, while the accumulated result keeps the node's return
    value identical to a plain ``llm.invoke(messages)`` so downstream logic
    (citation checks, persistence, evaluation) is unaffected.
    """
    accumulated: AIMessageChunk | None = None
    for chunk in llm.stream(messages):
        accumulated = chunk if accumulated is None else accumulated + chunk

    if accumulated is None:
        # Model yielded no chunks (e.g. empty completion); fall back to invoke.
        return llm.invoke(messages)
    return accumulated
