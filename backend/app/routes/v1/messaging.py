from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.routes.dependencies.messaging import get_send_message_service
from app.services.messaging import AgentType, SendMessageService
from app.utils import get_request_id

messaging_router = APIRouter(prefix="/messaging", tags=["messaging"])


@messaging_router.post("/send-message")
def send_message(
    query: str,
    agent_type: AgentType,
    request_id: Annotated[str, Depends(get_request_id)],
    send_message_service: Annotated[
        SendMessageService, Depends(get_send_message_service)
    ],
) -> StreamingResponse:
    return StreamingResponse(
        content=send_message_service.stream_message(
            query=query,
            agent_type=agent_type,
            request_id=request_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
