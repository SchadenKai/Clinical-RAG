import uuid
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.chat.context import AgentContext
from app.agent.chat.state import AgentState
from app.agent.chat.tools import clinical_retrieval_tool
from app.core.config import Settings
from app.db.chat import ChatRepository
from app.logger import app_logger
from app.services.llm.factory import ChatModelService
from app.services.rag import RetrievalService


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        chat_agent: CompiledStateGraph,
        retrieval_service: RetrievalService,
        chat_model_service: ChatModelService,
        settings: Settings,
    ):
        self.chat_repository = chat_repository
        self.chat_agent = chat_agent
        self.retrieval_service = retrieval_service
        self.chat_model_service = chat_model_service
        self.settings = settings

    def send_message(
        self,
        user_id: uuid.UUID,
        query: str,
        agent_id: str,
        session_id: Optional[str] = None,
        request_id: str = "",
    ) -> str:
        conversation = self.chat_repository.create_or_get_conversation(
            user_id, session_id
        )

        # Save user message
        self.chat_repository.save_message(
            conversation.id, role="user", content=query, agent_id=agent_id
        )

        history = self.chat_repository.get_conversation_history(conversation.id)

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        langchain_msgs = []
        agent_config = self.chat_repository.get_agent(agent_id)

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
        self.chat_repository.save_message(
            conversation.id, role="assistant", content=final_response, agent_id=agent_id
        )

        return final_response
