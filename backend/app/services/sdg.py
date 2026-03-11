from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.sdg.context import AgentContext as SdgAgentContext
from app.agent.sdg.state import AgentState as SdgAgentState
from app.core.config import Settings
from app.logger import app_logger
from app.rag.embeddings import EmbeddingService
from app.services.file_store.db import S3Service
from app.services.llm.factory import ChatModelService


class SDGService:
    def __init__(
        self,
        sdg_agent: CompiledStateGraph,
        llm_service: ChatModelService,
        embedding_service: EmbeddingService,
        s3_service: S3Service,
        settings: Settings,
    ):
        self.sdg_agent = sdg_agent
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.s3_service = s3_service
        self.settings = settings

    def generate(
        self,
        file_key: str,
        testset_size: int,
        request_id: str,
    ) -> dict:
        init_state = SdgAgentState(
            file_key=file_key,
            testset_size=testset_size,
        )
        context = SdgAgentContext(
            llm_service=self.llm_service,
            embedding_service=self.embedding_service,
            s3_service=self.s3_service,
            settings=self.settings,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}

        final_response: dict = {}
        for res in self.sdg_agent.stream(
            input=init_state, context=context, config=config
        ):
            for node_name, state in res.items():
                app_logger.info("SDG pipeline node completed: %s", node_name)
                final_response = state

        return final_response
