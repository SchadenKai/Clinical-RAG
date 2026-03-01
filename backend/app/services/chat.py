import uuid
from typing import Optional, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from app.agent.chat.context import AgentContext
from app.agent.chat.state import AgentState
from app.agent.chat.tools import clinical_retrieval_tool
from app.core.config import Settings
from app.db.models import Agent, ChatConversation, ChatMessage
from app.logger import app_logger
from app.services.llm.factory import ChatModelService
from app.services.rag import RetrievalService


class ChatService:
    def __init__(
        self,
        db: Session,
        chat_agent: CompiledStateGraph,
        retrieval_service: RetrievalService,
        chat_model_service: ChatModelService,
        settings: Settings,
    ):
        self.db = db
        self.chat_agent = chat_agent
        self.retrieval_service = retrieval_service
        self.chat_model_service = chat_model_service
        self.settings = settings

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

    def send_message(
        self,
        user_id: uuid.UUID,
        query: str,
        agent_id: str,
        session_id: Optional[str] = None,
        request_id: str = "",
    ) -> str:
        conversation = self.create_or_get_conversation(user_id, session_id)

        # Save user message
        self.save_message(
            conversation.id, role="user", content=query, agent_id=agent_id
        )

        history = self.get_conversation_history(conversation.id)

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        langchain_msgs = []
        agent_config = self.get_agent(agent_id)

        if agent_config and agent_config.prompt:
            langchain_msgs.append(SystemMessage(content=agent_config.prompt))

        for msg in history:
            if msg.role == "user":
                langchain_msgs.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_msgs.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                langchain_msgs.append(SystemMessage(content=msg.content))

        # Build Context
        runtime_tools = []
        if agent_config and "retrieval_tool" in agent_config.tools:
            runtime_tools.append(clinical_retrieval_tool)

        context = AgentContext(
            llm=self.chat_model_service.client,
            tools=runtime_tools,
            retrieval_service=self.retrieval_service,
            settings=self.settings,
        )

        # Invoke agent graph
        init_state = AgentState(messages=langchain_msgs)
        config: RunnableConfig = RunnableConfig(configurable={"thread_id": request_id})

        final_response = ""
        try:
            for res in self.chat_agent.stream(
                input=init_state, context=context, config=config
            ):
                for _node_name, state_update in res.items():
                    messages = (
                        state_update.messages
                        if isinstance(state_update, AgentState)
                        and hasattr(state_update, "messages")
                        else state_update.get("messages")
                    )
                    if messages:
                        final_message = messages[-1]
                        if hasattr(
                            final_message, "content"
                        ):
                            final_response = final_message.content
        except Exception as e:
            app_logger.error(f"Error during agent invocation: {str(e)}")
            final_response = f"An error occurred: {str(e)}"

        # Save AI reply
        self.save_message(
            conversation.id, role="assistant", content=final_response, agent_id=agent_id
        )

        return final_response
