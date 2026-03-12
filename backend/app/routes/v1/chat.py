import uuid
from typing import Annotated, Generator, Literal, cast

from ag_ui.core import (
    CustomEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from app.agent.react_agent.context import AgentContext as ReactAgentContext
from app.agent.react_agent.state import AgentState as ReactAgentState
from app.agent.retriever.context import AgentContext as RetrieverAgentContext
from app.agent.retriever.models import SafetyClassificationEnum
from app.agent.retriever.state import AgentState as RetrieverAgentState
from app.routes.dependencies.chat_service import get_chat_service
from app.routes.dependencies.rag import get_retrieval_service
from app.services.chat import ChatService
from app.services.rag import RetrievalService
from app.utils import get_request_id

chat_router = APIRouter(prefix="/chat", tags=["chat"])

# Human-readable labels for LangGraph node names
REACT_NODE_LABELS = {
    "validate_input_node": "Validating input",
    "call_llm_node": "Generating response",
}

RAG_NODE_LABELS = {
    "safety_classifier_node": "Classifying query safety",
    "refusal_node": "Generating refusal response",
    "generate_queries": "Generating search queries",
    "embed_query": "Embedding queries",
    "search": "Searching knowledge base",
    "rerank_node": "Reranking results",
    "final_report_generation": "Generating clinical report",
    "citation_verification": "Verifying citations",
}


class StreamChatRequest(BaseModel):
    query: str
    agent_id: Literal["general", "clinical_rag"] = "general"
    system_prompt: str = "You are a helpful assistant"
    is_llm_enabled: bool = True


@chat_router.post("")
def send_message(
    query: str,
    request_id: Annotated[str, Depends(get_request_id)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    system_prompt: str = "You are a helpful assistant",
):
    return chat_service.send_message(
        query=query, system_prompt=system_prompt, request_id=request_id
    )


def _stream_general_agent(
    chat_service: ChatService,
    body: StreamChatRequest,
    thread_id: str,
    message_id: str,
    encoder: EventEncoder,
) -> Generator[str, None, None]:
    chat_model = chat_service.chat_model_service.client
    init_state = ReactAgentState(
        messages=[
            SystemMessage(content=body.system_prompt),
            HumanMessage(content=body.query),
        ]
    )
    context = ReactAgentContext(llm=chat_model)
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    final_content = ""
    for res in chat_service.agent.stream(
        input=init_state, context=context, config=config
    ):
        for node_name, state_update in res.items():
            label = REACT_NODE_LABELS.get(node_name, node_name)
            yield encoder.encode(StepStartedEvent(step_name=label))

            if "messages" in state_update:
                final_message = cast(BaseMessage, state_update["messages"][-1])
                final_content = str(final_message.content)

            yield encoder.encode(StepFinishedEvent(step_name=label))

    if final_content:
        yield encoder.encode(
            TextMessageStartEvent(message_id=message_id, role="assistant")
        )
        yield encoder.encode(
            TextMessageContentEvent(message_id=message_id, delta=final_content)
        )
        yield encoder.encode(TextMessageEndEvent(message_id=message_id))


def _stream_clinical_rag_agent(
    retrieval_service: RetrievalService,
    body: StreamChatRequest,
    thread_id: str,
    message_id: str,
    encoder: EventEncoder,
) -> Generator[str, None, None]:
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

    accumulated_state: dict = {}
    for res in retrieval_service.retriever_agent.stream(
        input=init_state, context=context, config=config
    ):
        for node_name, state_update in res.items():
            label = RAG_NODE_LABELS.get(node_name, node_name)
            yield encoder.encode(StepStartedEvent(step_name=label))

            state_update = cast(dict, state_update)
            accumulated_state.update(state_update)

            # Emit intermediate data as CUSTOM events
            if (
                node_name == "safety_classifier_node"
                and "safety_classification" in state_update
            ):
                sc = state_update["safety_classification"]
                yield encoder.encode(
                    CustomEvent(
                        name="safety_classification",
                        value={
                            "classification": sc.classification.value if isinstance(sc.classification, SafetyClassificationEnum) else sc.classification,
                            "confidence_score": sc.confidence_score,
                            "supporting_args": sc.supporting_args,
                        },
                    )
                )

            if node_name == "rerank_node" and "documents" in state_update:
                clean_docs = []
                for doc in state_update["documents"]:
                    d = dict(doc)
                    d.pop("vector", None)
                    d.pop("sparse_vector", None)
                    clean_docs.append(d)
                yield encoder.encode(CustomEvent(name="documents", value=clean_docs))

            if "sources" in state_update:
                yield encoder.encode(
                    CustomEvent(name="sources", value=state_update["sources"])
                )

            # Remove large fields from accumulated state
            accumulated_state.pop("embedded_query", None)

            yield encoder.encode(StepFinishedEvent(step_name=label))

    # Stream the final answer as TEXT_MESSAGE events
    final_answer = accumulated_state.get("final_answer", "")
    if final_answer:
        yield encoder.encode(
            TextMessageStartEvent(message_id=message_id, role="assistant")
        )
        yield encoder.encode(
            TextMessageContentEvent(message_id=message_id, delta=final_answer)
        )
        yield encoder.encode(TextMessageEndEvent(message_id=message_id))


@chat_router.post("/stream")
def stream_chat(
    body: StreamChatRequest,
    request_id: Annotated[str, Depends(get_request_id)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
):
    encoder = EventEncoder()
    thread_id = request_id
    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    def event_generator():
        try:
            yield encoder.encode(RunStartedEvent(thread_id=thread_id, run_id=run_id))

            if body.agent_id == "general":
                yield from _stream_general_agent(
                    chat_service, body, thread_id, message_id, encoder
                )
            else:
                yield from _stream_clinical_rag_agent(
                    retrieval_service, body, thread_id, message_id, encoder
                )

            yield encoder.encode(RunFinishedEvent(thread_id=thread_id, run_id=run_id))
        except Exception as e:
            yield encoder.encode(RunErrorEvent(message=str(e), code="INTERNAL_ERROR"))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
