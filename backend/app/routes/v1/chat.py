import uuid
from collections.abc import Generator
from typing import Annotated

from ag_ui.core import (
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.routes.dependencies.agent_service import get_agent_service
from app.routes.dependencies.chat_service import get_chat_service
from app.routes.dependencies.rag import get_retrieval_service
from app.routes.v1.chat_stream import (
    stream_clinical_rag_agent,
    stream_general_agent,
)
from app.services.agent import AgentService
from app.services.chat import ChatService
from app.services.rag import RetrievalService
from app.utils import get_request_id

chat_router = APIRouter(prefix="/chat", tags=["chat"])


class StreamChatRequest(BaseModel):
    query: str
    # Any agent id persisted via the agents API. Defaults to the seeded
    # "general" agent. The backend resolves the agent's stored prompt/pipeline;
    # ``system_prompt`` is only a fallback when the agent has no prompt set.
    agent_id: str = "general"
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


@chat_router.post("/stream")
def stream_chat(
    body: StreamChatRequest,
    request_id: Annotated[str, Depends(get_request_id)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> StreamingResponse:
    # Resolve the selected agent up-front so a bad id returns a clean 404 rather
    # than failing mid-stream. Capture plain values: the DB session closes when
    # this function returns, before the generator below runs.
    agent = agent_service.get_agent(body.agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{body.agent_id}' not found",
        )
    pipeline = agent.pipeline
    effective_body = body.model_copy(
        update={"system_prompt": agent.prompt or body.system_prompt}
    )

    encoder = EventEncoder()
    thread_id = request_id
    run_id = str(uuid.uuid4())

    def event_generator() -> Generator[str, None, None]:
        try:
            yield encoder.encode(RunStartedEvent(thread_id=thread_id, run_id=run_id))

            if pipeline == "clinical_rag":
                yield from stream_clinical_rag_agent(
                    retrieval_service, effective_body, thread_id, encoder
                )
            else:
                yield from stream_general_agent(
                    chat_service, effective_body, thread_id, encoder
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
