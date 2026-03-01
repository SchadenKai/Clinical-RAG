from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.models import Agent
from app.routes.dependencies.auth import get_current_user
from app.routes.dependencies.chat_service import get_chat_service
from app.services.chat import ChatService
from app.utils import get_request_id

chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequestBody(BaseModel):
    query: str
    session_id: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    title: str


@chat_router.post("")
def send_message(
    payload: ChatRequestBody,
    request_id: Annotated[str, Depends(get_request_id)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
    agent_id: str = Query("general", description="ID of the agent to use"),
):
    # 1. Look up agent in DB
    agent_config = chat_service.chat_repository.get_agent(agent_id)
    if not agent_config:
        if agent_id == "general":
            agent_config = Agent(id="general", name="General Chat", tools=[])
            chat_service.chat_repository.db.add(agent_config)
            chat_service.chat_repository.db.commit()
            chat_service.chat_repository.db.refresh(agent_config)
        elif agent_id == "clinical_rag":
            agent_config = Agent(
                id="clinical_rag", name="Clinical RAG", tools=["retrieval_tool"]
            )
            chat_service.chat_repository.db.add(agent_config)
            chat_service.chat_repository.db.commit()
            chat_service.chat_repository.db.refresh(agent_config)
        else:
            raise HTTPException(status_code=404, detail="Agent not found")

    # 2. Execute
    response = chat_service.send_message(
        user_id=current_user.id,
        query=payload.query,
        agent_id=agent_id,
        session_id=payload.session_id,
        request_id=request_id,
    )

    return {"response": response}


@chat_router.get("/sessions")
def list_sessions(
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    from app.db.models import ChatConversation

    sessions = (
        chat_service.chat_repository.db.query(ChatConversation)
        .filter(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.created_at.desc())
        .all()
    )
    return {
        "sessions": [
            {"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions
        ]
    }


@chat_router.post("/sessions")
def create_session(
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
    title: str = Query("New Chat"),
):
    conv = chat_service.chat_repository.create_or_get_conversation(
        user_id=current_user.id, title=title
    )
    return {"session_id": conv.id, "title": conv.title}


@chat_router.patch("/sessions/{session_id}")
def update_session(
    session_id: str,
    payload: UpdateSessionRequest,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    from app.db.models import ChatConversation

    conv = (
        chat_service.chat_repository.db.query(ChatConversation)
        .filter(
            ChatConversation.id == session_id,
            ChatConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    conv.title = payload.title
    chat_service.chat_repository.db.commit()
    chat_service.chat_repository.db.refresh(conv)

    return {"session_id": conv.id, "title": conv.title}


@chat_router.get("/sessions/{session_id}")
def get_session_messages(
    session_id: str,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    messages = chat_service.chat_repository.get_conversation_history(session_id)
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "agent_id": m.agent_id,
            }
            for m in messages
        ]
    }


@chat_router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    from app.db.models import ChatConversation

    conv = (
        chat_service.chat_repository.db.query(ChatConversation)
        .filter(
            ChatConversation.id == session_id,
            ChatConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    chat_service.chat_repository.db.delete(conv)
    chat_service.chat_repository.db.commit()
    return {"message": "Session deleted"}


@chat_router.delete("/sessions/{session_id}/messages/{msg_id}")
def delete_message(
    session_id: str,
    msg_id: str,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    from app.db.models import ChatConversation, ChatMessage

    # Verify ownership
    conv = (
        chat_service.chat_repository.db.query(ChatConversation)
        .filter(
            ChatConversation.id == session_id,
            ChatConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    msg = (
        chat_service.chat_repository.db.query(ChatMessage)
        .filter(
            ChatMessage.id == msg_id,
            ChatMessage.conversation_id == session_id,
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    chat_service.chat_repository.db.delete(msg)
    chat_service.chat_repository.db.commit()
    return {"message": "Message deleted"}
