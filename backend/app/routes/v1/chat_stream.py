"""AG-UI streaming generators for the chat endpoints.

Translates a LangGraph run into Agent-User Interaction (AG-UI) protocol events
so the frontend gets a rich, real-time view of what the agent is doing:

* ``STEP_STARTED`` / ``STEP_FINISHED`` -- in-progress lifecycle for each
  pipeline stage.
* ``TOOL_CALL_*`` -- genuine tool calls for the RAG pipeline
  (``search_knowledge_base`` and ``rerank_documents``) with arguments and
  results.
* ``TEXT_MESSAGE_*`` -- real token-by-token streaming of the assistant answer.
* ``CUSTOM`` -- side-channel data (safety classification, documents, sources).

Both generators consume LangGraph's multi-mode stream
(``stream_mode=["updates", "messages"]``). ``messages`` payloads carry LLM
token chunks; ``updates`` payloads carry the per-node state deltas that drive
step, tool, and custom events.
"""

import json
import uuid
from typing import TYPE_CHECKING, Generator

from ag_ui.core import (
    CustomEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agent.react_agent.context import AgentContext as ReactAgentContext
from app.agent.react_agent.state import AgentState as ReactAgentState
from app.agent.retriever.context import AgentContext as RetrieverAgentContext
from app.agent.retriever.models import SafetyClassificationEnum
from app.agent.retriever.state import AgentState as RetrieverAgentState
from app.services.chat import ChatService
from app.services.rag import RetrievalService

if TYPE_CHECKING:
    from app.routes.v1.chat import StreamChatRequest

# Human-readable labels for LangGraph node names.
_REACT_NODE_LABELS = {
    "validate_input_node": "Validating input",
    "call_llm_node": "Generating response",
}

_RAG_NODE_LABELS = {
    "safety_classifier_node": "Classifying query safety",
    "refusal_node": "Generating refusal response",
    "generate_queries": "Generating search queries",
    "embed_query": "Embedding queries",
    "search": "Searching knowledge base",
    "rerank_node": "Reranking results",
    "final_report_generation": "Generating clinical report",
    "citation_verification": "Verifying citations",
    "llm_judge_node": "Evaluating answer quality",
}

# Nodes whose LLM tokens are streamed to the user as the assistant message.
_GENERAL_FINAL_NODES = {"call_llm_node"}
_RAG_FINAL_NODES = {"final_report_generation", "refusal_node"}

_MAX_RESULT_SOURCES = 10


def _as_dict(state_update: object) -> dict:
    """Normalise a LangGraph node update (dict or Pydantic model) to a dict."""
    if isinstance(state_update, dict):
        return state_update
    try:
        return dict(state_update)  # type: ignore[arg-type]
    except TypeError:
        return {}


def _chunk_text(content: object) -> str:
    """Extract plain text from a message chunk's content (str or block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


def _unique_sources(sources: object, limit: int = _MAX_RESULT_SOURCES) -> list:
    """Return up to ``limit`` unique, truthy sources preserving order."""
    if not isinstance(sources, list):
        return []
    seen: list = []
    for source in sources:
        if source and source not in seen:
            seen.append(source)
        if len(seen) >= limit:
            break
    return seen


class _TextStream:
    """Tracks the currently open AG-UI text message for token streaming.

    A new message is opened lazily on the first non-empty token and closed
    explicitly. If a final-answer node re-runs (citation/judge retries), the
    caller closes the previous message and a fresh one is opened, so the client
    naturally replaces the in-progress answer.
    """

    def __init__(self, encoder: EventEncoder):
        self._encoder = encoder
        self.message_id: str | None = None

    def push(self, text: str) -> Generator[str, None, None]:
        if not text:
            return
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
            yield self._encoder.encode(
                TextMessageStartEvent(message_id=self.message_id, role="assistant")
            )
        yield self._encoder.encode(
            TextMessageContentEvent(message_id=self.message_id, delta=text)
        )

    def close(self) -> Generator[str, None, None]:
        if self.message_id is not None:
            yield self._encoder.encode(TextMessageEndEvent(message_id=self.message_id))
            self.message_id = None


def _step_events(
    encoder: EventEncoder, node_name: str, labels: dict[str, str]
) -> Generator[str, None, None]:
    """Emit the start/finish lifecycle for a completed pipeline step."""
    label = labels.get(node_name, node_name)
    yield encoder.encode(StepStartedEvent(step_name=label))
    yield encoder.encode(StepFinishedEvent(step_name=label))


def _rerank_tool_events(
    encoder: EventEncoder, update: dict
) -> Generator[str, None, None]:
    """Emit a self-contained ``rerank_documents`` tool-call lifecycle."""
    tool_call_id = str(uuid.uuid4())
    documents = update.get("documents") or []
    yield encoder.encode(
        ToolCallStartEvent(
            tool_call_id=tool_call_id, tool_call_name="rerank_documents"
        )
    )
    yield encoder.encode(
        ToolCallArgsEvent(
            tool_call_id=tool_call_id,
            delta=json.dumps({"top_k": len(documents)}),
        )
    )
    yield encoder.encode(ToolCallEndEvent(tool_call_id=tool_call_id))
    yield encoder.encode(
        ToolCallResultEvent(
            message_id=str(uuid.uuid4()),
            tool_call_id=tool_call_id,
            content=json.dumps(
                {
                    "reranked_count": len(documents),
                    "top_sources": _unique_sources(update.get("sources")),
                }
            ),
        )
    )


def _rag_custom_events(
    encoder: EventEncoder, node_name: str, update: dict
) -> Generator[str, None, None]:
    """Emit CUSTOM side-channel events (safety, documents, sources)."""
    if node_name == "safety_classifier_node" and "safety_classification" in update:
        sc = update["safety_classification"]
        classification = (
            sc.classification.value
            if isinstance(sc.classification, SafetyClassificationEnum)
            else sc.classification
        )
        yield encoder.encode(
            CustomEvent(
                name="safety_classification",
                value={
                    "classification": classification,
                    "confidence_score": sc.confidence_score,
                    "supporting_args": sc.supporting_args,
                },
            )
        )

    if node_name == "rerank_node" and update.get("documents"):
        clean_docs = []
        for doc in update["documents"]:
            d = dict(doc)
            d.pop("vector", None)
            d.pop("sparse_vector", None)
            clean_docs.append(d)
        yield encoder.encode(CustomEvent(name="documents", value=clean_docs))

    if update.get("sources"):
        yield encoder.encode(CustomEvent(name="sources", value=update["sources"]))


def stream_general_agent(
    chat_service: ChatService,
    body: "StreamChatRequest",
    thread_id: str,
    encoder: EventEncoder,
) -> Generator[str, None, None]:
    """Stream the general (non-RAG) react agent as AG-UI events."""
    chat_model = chat_service.chat_model_service.client
    init_state = ReactAgentState(
        messages=[
            SystemMessage(content=body.system_prompt),
            HumanMessage(content=body.query),
        ]
    )
    context = ReactAgentContext(llm=chat_model)
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    text = _TextStream(encoder)
    for mode, payload in chat_service.agent.stream(
        input=init_state,
        context=context,
        config=config,
        stream_mode=["updates", "messages"],
    ):
        if mode == "messages":
            chunk, metadata = payload
            if metadata.get("langgraph_node") in _GENERAL_FINAL_NODES:
                yield from text.push(_chunk_text(chunk.content))
            continue

        for node_name in payload:
            if node_name in _GENERAL_FINAL_NODES:
                yield from text.close()
                continue
            yield from _step_events(encoder, node_name, _REACT_NODE_LABELS)

    yield from text.close()


def stream_clinical_rag_agent(
    retrieval_service: RetrievalService,
    body: "StreamChatRequest",
    thread_id: str,
    encoder: EventEncoder,
) -> Generator[str, None, None]:
    """Stream the clinical RAG retriever agent as AG-UI events."""
    db_client = retrieval_service.vector_db_service.client
    chat_model = retrieval_service.chat_model_service.client

    init_state = RetrieverAgentState(input_query=body.query)
    context = RetrieverAgentContext(
        embedding=retrieval_service.embedding_service,
        tokenizer=retrieval_service.tokenizer_service,
        db_client=db_client,
        chat_model=chat_model,
        reranker=retrieval_service.reranker_service,
        include_generation=body.is_llm_enabled,
        settings=retrieval_service.settings,
    )
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    text = _TextStream(encoder)
    search_tool_id: str | None = None

    for mode, payload in retrieval_service.retriever_agent.stream(
        input=init_state,
        context=context,
        config=config,
        stream_mode=["updates", "messages"],
    ):
        if mode == "messages":
            chunk, metadata = payload
            if metadata.get("langgraph_node") in _RAG_FINAL_NODES:
                yield from text.push(_chunk_text(chunk.content))
            continue

        for node_name, raw_update in payload.items():
            update = _as_dict(raw_update)

            # Close the streamed answer when its node finishes (handles retries).
            if node_name in _RAG_FINAL_NODES:
                yield from text.close()

            # search_knowledge_base opens once queries are ready (before the
            # slow embed/search work) so the client shows it as in-progress...
            if node_name == "generate_queries" and update.get("generated_queries"):
                search_tool_id = str(uuid.uuid4())
                yield encoder.encode(
                    ToolCallStartEvent(
                        tool_call_id=search_tool_id,
                        tool_call_name="search_knowledge_base",
                    )
                )
                yield encoder.encode(
                    ToolCallArgsEvent(
                        tool_call_id=search_tool_id,
                        delta=json.dumps({"queries": update["generated_queries"]}),
                    )
                )

            # ...and closes once the search node returns documents.
            if node_name == "search" and search_tool_id is not None:
                documents = update.get("documents") or []
                yield encoder.encode(ToolCallEndEvent(tool_call_id=search_tool_id))
                yield encoder.encode(
                    ToolCallResultEvent(
                        message_id=str(uuid.uuid4()),
                        tool_call_id=search_tool_id,
                        content=json.dumps(
                            {
                                "document_count": len(documents),
                                "sources": _unique_sources(update.get("sources")),
                            }
                        ),
                    )
                )
                search_tool_id = None

            if node_name == "rerank_node" and update.get("documents"):
                yield from _rerank_tool_events(encoder, update)

            yield from _step_events(encoder, node_name, _RAG_NODE_LABELS)
            yield from _rag_custom_events(encoder, node_name, update)

    yield from text.close()
