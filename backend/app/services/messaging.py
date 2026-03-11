import uuid
from collections.abc import Generator
from enum import Enum
from typing import cast

from ag_ui.core import (
    CustomEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.react_agent.context import AgentContext as ReactAgentContext
from app.agent.react_agent.state import AgentState as ReactAgentState
from app.agent.retriever.context import AgentContext as InferenceAgentContext
from app.agent.retriever.state import AgentState as InferenceAgentState
from app.core.config import Settings
from app.logger import app_logger
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.services.llm.factory import ChatModelService
from app.services.llm.tokenizer import TokenizerService
from app.services.reranking import RerankerService


class AgentType(str, Enum):
    CLINICAL_GUIDELINE = "clinical_guideline"
    GENERAL = "general"


class SendMessageService:
    def __init__(
        self,
        retriever_agent: CompiledStateGraph,
        react_agent: CompiledStateGraph,
        embedding_service: EmbeddingService,
        vector_db_service: VectorClient,
        tokenizer_service: TokenizerService,
        chat_model_service: ChatModelService,
        reranker_service: RerankerService,
        settings: Settings,
    ):
        self.retriever_agent = retriever_agent
        self.react_agent = react_agent
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.tokenizer_service = tokenizer_service
        self.chat_model_service = chat_model_service
        self.reranker_service = reranker_service
        self.settings = settings

    def stream_message(
        self,
        query: str,
        agent_type: AgentType,
        request_id: str,
    ) -> Generator[str, None, None]:
        encoder = EventEncoder()
        thread_id = request_id
        run_id = str(uuid.uuid4())

        yield encoder.encode(
            RunStartedEvent(thread_id=thread_id, run_id=run_id)
        )

        try:
            if agent_type == AgentType.CLINICAL_GUIDELINE:
                yield from self._stream_retriever_agent(
                    query=query,
                    thread_id=thread_id,
                    run_id=run_id,
                    request_id=request_id,
                    encoder=encoder,
                )
            elif agent_type == AgentType.GENERAL:
                yield from self._stream_react_agent(
                    query=query,
                    thread_id=thread_id,
                    run_id=run_id,
                    request_id=request_id,
                    encoder=encoder,
                )
            else:
                yield encoder.encode(
                    RunErrorEvent(message=f"Unknown agent type: {agent_type}")
                )
                return

            yield encoder.encode(
                RunFinishedEvent(thread_id=thread_id, run_id=run_id)
            )
        except Exception as e:
            app_logger.error("Error in stream_message: %s", e, exc_info=True)
            yield encoder.encode(RunErrorEvent(message=str(e)))

    def _stream_retriever_agent(
        self,
        query: str,
        thread_id: str,
        run_id: str,
        request_id: str,
        encoder: EventEncoder,
    ) -> Generator[str, None, None]:
        db_client = self.vector_db_service.client
        chat_model = self.chat_model_service.client

        init_state = InferenceAgentState(input_query=query)
        context = InferenceAgentContext(
            embedding=self.embedding_service,
            tokenizer=self.tokenizer_service,
            db_client=db_client,
            chat_model=chat_model,
            reranker=self.reranker_service,
            include_generation=True,
            settings=self.settings,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}

        # ── Phase 1: stream_mode="updates" ──
        # Run the graph with updates mode to get state after each node.
        # Collect the final state from each node for emitting step events.
        accumulated_state: dict = {}
        message_id = str(uuid.uuid4())
        is_streaming_text = False

        for mode, chunk in self.retriever_agent.stream(
            input=init_state,
            context=context,
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "updates":
                for node_name, state_update in chunk.items():
                    yield encoder.encode(StepStartedEvent(step_name=node_name))

                    state_update = cast(dict, state_update)

                    # Remove embedded_query from state snapshots (too large)
                    if state_update.get("embedded_query"):
                        state_update.pop("embedded_query")

                    accumulated_state.update(state_update)

                    yield encoder.encode(
                        StateSnapshotEvent(snapshot=accumulated_state)
                    )
                    yield encoder.encode(StepFinishedEvent(step_name=node_name))

            elif mode == "messages":
                ai_chunk, metadata = chunk
                # Only stream text from final_report_generation node
                if (
                    isinstance(ai_chunk, AIMessageChunk)
                    and metadata.get("langgraph_node") == "final_report_generation"
                ):
                    content = (
                        ai_chunk.content
                        if isinstance(ai_chunk.content, str)
                        else ""
                    )
                    if content:
                        if not is_streaming_text:
                            yield encoder.encode(
                                TextMessageStartEvent(
                                    message_id=message_id, role="assistant"
                                )
                            )
                            is_streaming_text = True

                        yield encoder.encode(
                            TextMessageContentEvent(
                                message_id=message_id, delta=content
                            )
                        )

        if is_streaming_text:
            yield encoder.encode(TextMessageEndEvent(message_id=message_id))

        # Emit final state snapshot with the complete response data
        # structured to match /rag/retrieve output format
        final_snapshot = self._build_retriever_response(accumulated_state)
        yield encoder.encode(
            CustomEvent(name="final_response", value=final_snapshot)
        )

    def _stream_react_agent(
        self,
        query: str,
        thread_id: str,
        run_id: str,
        request_id: str,
        encoder: EventEncoder,
    ) -> Generator[str, None, None]:
        chat_model = self.chat_model_service.client

        init_state = ReactAgentState(
            messages=[
                SystemMessage(content="You are a helpful assistant"),
                HumanMessage(content=query),
            ]
        )
        react_context = ReactAgentContext(llm=chat_model)
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}

        message_id = str(uuid.uuid4())
        is_streaming_text = False

        for mode, chunk in self.react_agent.stream(
            input=init_state,
            context=react_context,
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "updates":
                for node_name, _state_update in chunk.items():
                    yield encoder.encode(StepStartedEvent(step_name=node_name))
                    yield encoder.encode(StepFinishedEvent(step_name=node_name))

            elif mode == "messages":
                ai_chunk, metadata = chunk
                if (
                    isinstance(ai_chunk, AIMessageChunk)
                    and metadata.get("langgraph_node") == "call_llm_node"
                ):
                    content = (
                        ai_chunk.content
                        if isinstance(ai_chunk.content, str)
                        else ""
                    )
                    if content:
                        if not is_streaming_text:
                            yield encoder.encode(
                                TextMessageStartEvent(
                                    message_id=message_id, role="assistant"
                                )
                            )
                            is_streaming_text = True

                        yield encoder.encode(
                            TextMessageContentEvent(
                                message_id=message_id, delta=content
                            )
                        )

        if is_streaming_text:
            yield encoder.encode(TextMessageEndEvent(message_id=message_id))

    @staticmethod
    def _build_retriever_response(state: dict) -> dict:
        """Build a response dict matching the /rag/retrieve output format."""
        return {
            "input_query": state.get("input_query"),
            "generated_queries": state.get("generated_queries"),
            "final_answer": state.get("final_answer"),
            "documents": state.get("documents"),
            "sources": state.get("sources"),
            "safety_classification": state.get("safety_classification"),
            "is_verified_citations": state.get("is_verified_citations"),
            "wrong_citations": state.get("wrong_citations"),
            "run_metadata": state.get("run_metadata"),
        }
