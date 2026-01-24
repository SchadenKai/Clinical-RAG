from typing import cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.indexing.context import AgentContext as IndexingAgentContext
from app.agent.indexing.state import AgentState as IndexingAgentState
from app.agent.retriever.context import AgentContext as InferenceAgentContext
from app.agent.retriever.state import AgentState as InferenceAgentState
from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.services.llm.factory import ChatModelService
from app.services.llm.tokenizer import TokenizerService


class IndexingService:
    def __init__(
        self,
        chunker_service: ChunkerService,
        embedding_service: EmbeddingService,
        vector_db_service: VectorClient,
        tokenizer_service: TokenizerService,
        indexing_agent: CompiledStateGraph,
        settings: Settings,
    ):
        self.chunker_service: ChunkerService = chunker_service
        self.embedding_service: EmbeddingService = embedding_service
        self.vector_db_service: VectorClient = vector_db_service
        self.tokenizer_service: TokenizerService = tokenizer_service
        self.indexing_agent: CompiledStateGraph = indexing_agent
        self.settings: Settings = settings

    def ingest_document(self, website_url: str, request_id: str) -> IndexingAgentState:
        collection_name = self.settings.milvus_collection_name
        db_client = self.vector_db_service.client

        init_state = IndexingAgentState(website_url=website_url)
        context = IndexingAgentContext(
            chunker=self.chunker_service.get("recursive"),
            embedding=self.embedding_service,
            tokenizer=self.tokenizer_service,
            db_client=db_client,
            collection_name=collection_name,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}
        final_response = {}
        for res in self.indexing_agent.stream(
            input=init_state, context=context, config=config
        ):
            for node_name, state in res.items():
                if "indexing_node" in node_name:
                    final_response = state["run_metadata"]
        return final_response


class RetrievalService:
    def __init__(
        self,
        retriever_agent: CompiledStateGraph,
        chunker_service: ChunkerService,
        embedding_service: EmbeddingService,
        vector_db_service: VectorClient,
        tokenizer_service: TokenizerService,
        chat_model_service: ChatModelService,
        settings: Settings,
    ):
        self.retriever_agent: CompiledStateGraph = retriever_agent
        self.chunker_service: ChunkerService = chunker_service
        self.embedding_service: EmbeddingService = embedding_service
        self.vector_db_service: VectorClient = vector_db_service
        self.tokenizer_service: TokenizerService = tokenizer_service
        self.chat_model_service: ChatModelService = chat_model_service
        self.settings: Settings = settings

    def retrieve_documents(
        self,
        query: str,
        request_id: str,
        is_llm_enabled: bool = False,
    ) -> InferenceAgentState:
        collection_name = self.settings.milvus_collection_name
        db_client = self.vector_db_service.client
        chat_model = self.chat_model_service.client

        init_state = InferenceAgentState(input_query=query)
        context = InferenceAgentContext(
            chunker=self.chunker_service.get("recursive"),
            embedding=self.embedding_service,
            tokenizer=self.tokenizer_service,
            db_client=db_client,
            chat_model=chat_model,
            collection_name=collection_name,
            include_generation=is_llm_enabled,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}
        final_response = {}
        for res in self.retriever_agent.stream(
            input=init_state, context=context, config=config
        ):
            for _, state in res.items():
                if state.get("embedded_query"):
                    state = cast(dict, state)
                    state.pop("embedded_query")
                final_response = state
        return final_response
