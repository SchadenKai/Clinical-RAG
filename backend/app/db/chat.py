import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Agent, ChatConversation, ChatMessage


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def create_or_get_conversation(
        self,
        user_id: uuid.UUID,
        session_id: Optional[str] = None,
        title: str = "New Chat",
    ) -> ChatConversation:
        if session_id:
            conv = (
                self.db.query(ChatConversation)
                .filter(
                    ChatConversation.id == session_id,
                    ChatConversation.user_id == user_id,
                )
                .first()
            )
            if conv:
                return conv

        new_conv = ChatConversation(user_id=user_id, title=title)
        self.db.add(new_conv)
        self.db.commit()
        self.db.refresh(new_conv)
        return new_conv

    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_id=agent_id,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_conversation_history(self, conversation_id: str) -> list[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
