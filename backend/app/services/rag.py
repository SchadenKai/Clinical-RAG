import asyncio
import random
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.indexing.context import AgentContext as IndexingAgentContext
from app.agent.indexing.state import AgentState as IndexingAgentState
from app.agent.retriever.context import AgentContext as InferenceAgentContext
from app.agent.retriever.state import AgentState as InferenceAgentState
from app.core.config import Settings
from app.logger import app_logger
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.services.file_store.context_manager import FileStager
from app.services.file_store.db import S3Service
from app.services.llm.factory import ChatModelService
from app.services.llm.tokenizer import TokenizerService
from app.services.scrapper import document_extractor, simple_crawler


class IndexingService:
    def __init__(
        self,
        chunker_service: ChunkerService,
        embedding_service: EmbeddingService,
        vector_db_service: VectorClient,
        tokenizer_service: TokenizerService,
        indexing_agent: CompiledStateGraph,
        s3_service: S3Service,
        settings: Settings,
    ):
        self.chunker_service: ChunkerService = chunker_service
        self.embedding_service: EmbeddingService = embedding_service
        self.vector_db_service: VectorClient = vector_db_service
        self.tokenizer_service: TokenizerService = tokenizer_service
        self.indexing_agent: CompiledStateGraph = indexing_agent
        self.s3_service: S3Service = s3_service
        self.settings: Settings = settings

    def upload_file(self, pdf_file: SpooledTemporaryFile, filename: str) -> None:
        s3_client = self.s3_service.client
        try:
            s3_client.upload_fileobj(
                pdf_file, self.settings.minio_bucket_name, filename
            )
            return None
        except Exception as e:
            app_logger.error(
                f"Something went wrong during uploading of file to file store: {e}"
            )
            return None

    def get_object_list(self, file_name: str) -> list[str]:
        s3_client = self.s3_service.client
        if file_name:
            objects = s3_client.list_objects(
                Bucket=self.settings.minio_bucket_name, Prefix=file_name
            )
        else:
            objects = s3_client.list_objects(Bucket=self.settings.minio_bucket_name)
        return (
            [obj["Key"] for obj in objects["Contents"]]
            if objects.get("Contents")
            else []
        )

    def ingest_document(self, file_key: str, request_id: str) -> IndexingAgentState:
        db_client = self.vector_db_service.client

        init_state = IndexingAgentState(file_key=file_key)
        context = IndexingAgentContext(
            chunker=self.chunker_service.get(
                chunker_name="recursive", chunk_size=1021, chunk_overlap=10
            ),
            embedding=self.embedding_service,
            tokenizer=self.tokenizer_service,
            db_client=db_client,
            settings=self.settings,
            s3_service=self.s3_service,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}
        final_response = {}
        for res in self.indexing_agent.stream(
            input=init_state, context=context, config=config
        ):
            for node_name, state in res.items():
                # consideration for early outs
                if "is_chunked_docs_empty" in node_name:
                    final_response = state
                if "indexing_node" in node_name:
                    state = cast(dict, state)
                    state.pop("final_documents")
                    final_response = state
        return final_response

    def ingest_website(
        self,
        website_url: str,
        request_id: str,
    ) -> IndexingAgentState:
        db_client = self.vector_db_service.client

        init_state = IndexingAgentState(website_url=website_url)
        context = IndexingAgentContext(
            chunker=self.chunker_service.get(
                chunker_name="recursive", chunk_size=1021, chunk_overlap=10
            ),
            embedding=self.embedding_service,
            tokenizer=self.tokenizer_service,
            db_client=db_client,
            settings=self.settings,
            s3_service=self.s3_service,
        )
        config: RunnableConfig = {"configurable": {"thread_id": request_id}}
        final_response = {}
        for res in self.indexing_agent.stream(
            input=init_state, context=context, config=config
        ):
            for node_name, state in res.items():
                # consideration for early outs
                if "is_chunked_docs_empty" in node_name:
                    final_response = state
                if "indexing_node" in node_name:
                    state = cast(dict, state)
                    state.pop("final_documents")
                    final_response = state
        return final_response

    def test_scrapping_and_extraction(
        self,
        website_url: str,
    ) -> str:
        result = asyncio.run(simple_crawler(website_url))
        result = result.html
        file_name = f"test_{website_url}-{random.randint(1, 128)}"
        with FileStager(filename=file_name, temp_file_content=result) as file_path:
            result = document_extractor(file_path)
        return result.export_to_markdown()

    def test_doc_extraction(
        self, file_name: str, file: BinaryIO | None = None, file_url: str | None = None
    ) -> str:
        if file_url:
            result = document_extractor(file_url)
        else:
            with FileStager(
                filename=file_name, temp_file_content=file.read()
            ) as file_path:
                result = document_extractor(file_path)
        return result.export_to_markdown()


class RetrievalService:
    def __init__(
        self,
        retriever_agent: CompiledStateGraph,
        chunker_service: ChunkerService,
        embedding_service: EmbeddingService,
        vector_db_service: VectorClient,
        tokenizer_service: TokenizerService,
        settings: Settings,
        chat_model_service: ChatModelService,
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
