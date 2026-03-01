import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class ClinicalOccupation(str, enum.Enum):
    PHYSICIAN = "Physician"
    NURSE = "Nurse"
    PHARMACIST = "Pharmacist"
    SURGEON = "Surgeon"
    MEDICAL_STUDENT = "Medical Student"
    RESEARCHER = "Researcher"
    OTHER = "Other"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    occupation = Column(Enum(ClinicalOccupation), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_conversations = relationship(
        "ChatConversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # e.g. "general", "clinical_rag"
    name = Column(String, nullable=False)
    prompt = Column(String, nullable=True)
    tools = Column(JSON, default=list)  # list of strings: ["retrieval_tool", ...]
    starting_prompt_templates = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_conversations")
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String,
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id = Column(
        String,
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    role = Column(String, nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(String, nullable=False)
    token_count = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    # "metadata" is reserved in SQLAlchemy, so we alias the column
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, nullable=False, index=True)  # who, cdc, upload, web
    filename = Column(String, nullable=False)
    url = Column(String, nullable=True)
    # PENDING, INDEXING, INDEXED, FAILED
    status = Column(String, default="PENDING", index=True)
    metadata_ = Column("metadata", JSON, default=dict)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IndexingConfig(Base):
    __tablename__ = "indexing_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_strategy = Column(String, default="hybrid_hierarchal")
    chunk_size = Column(Integer, default=1024)
    chunk_overlap = Column(Integer, default=0)
    is_active = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    api_key = Column(String, nullable=True)  # In prod, should be encrypted
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmbeddingConfig(Base):
    __tablename__ = "embedding_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    api_key = Column(String, nullable=True)  # In prod, should be encrypted
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
