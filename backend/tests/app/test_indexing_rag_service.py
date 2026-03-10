import pytest
from docling_core.transforms.chunker.base import BaseChunker
from langgraph.graph.state import CompiledStateGraph
from pymilvus import MilvusClient
from pytest_mock import MockerFixture, MockType

from app.agent.indexing.models import RelevantDocs
from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.services.file_store.db import S3Service
from app.services.llm.tokenizer import TokenizerService
from app.services.rag import IndexingService


class TestIndexingRAGService:
    @pytest.fixture
    def indexing_service(self, mocker: MockerFixture) -> IndexingService:
        fake_chunker: MockType = mocker.Mock(spec=BaseChunker)
        fake_vector_client: MockType = mocker.Mock(spec=MilvusClient)

        mk_chunker_service: MockType = mocker.Mock(spec=ChunkerService)
        mk_chunker_service.get.return_value = fake_chunker
        mk_embedding_service: MockType = mocker.Mock(spec=EmbeddingService)

        mk_vector_db_service: MockType = mocker.Mock(spec=VectorClient)
        mk_vector_db_service.client = fake_vector_client

        mk_tokenizer_service: MockType = mocker.Mock(spec=TokenizerService)

        mk_s3_service: MockType = mocker.Mock(spec=S3Service)

        mk_indexing_agent: MockType = mocker.Mock(spec=CompiledStateGraph)
        mk_indexing_agent.stream.return_value = [
            {
                "indexing_node": {
                    "website_url": "https://google.com",
                    "raw_document": None,
                    "chunked_documents": None,
                    "final_documents": [
                        RelevantDocs(
                            text="testing 1",
                            vector=[0.123, -0.456, 0.789, 1.0],
                            source="https://google.com",
                        ),
                        RelevantDocs(
                            text="testing 2",
                            vector=[0.123, -0.456, 0.789, 1.0],
                            source="https://google.com",
                        ),
                    ],
                    "progress_status": "Done",
                    "run_metadata": {
                        "token_count": 123.00,
                        "total_cost": 123.00,
                        "duration_ms": 123.00,
                        "event": "test indexing",
                    },
                    "pipeline_metadata": {
                        "source": "https://google.com",
                        "page_title": "Test Page",
                        "source_type": "web",
                    },
                    "chunk_metadata_list": None,
                },
            }
        ]

        mk_settings: MockType = mocker.Mock(spec=Settings)
        mk_settings.milvus_collection_name = "collection_name"
        mk_settings.openai_api_key = "fake_api_key"
        mk_settings.chunk_size = 1021
        mk_settings.embedding_model = "text-embedding-3-small"

        return IndexingService(
            chunker_service=mk_chunker_service,
            embedding_service=mk_embedding_service,
            indexing_agent=mk_indexing_agent,
            tokenizer_service=mk_tokenizer_service,
            vector_db_service=mk_vector_db_service,
            s3_service=mk_s3_service,
            settings=mk_settings,
        )

    def test_upload_file(self, indexing_service: IndexingService):
        s3_client = indexing_service.s3_service.client
        s3_client.upload_fileobj("test", "test", "test")
        s3_client.upload_fileobj.assert_called_once_with("test", "test", "test")

    def test_ingestion_return_run_metadata_only(
        self, indexing_service: IndexingService
    ):
        result = indexing_service.ingest_website(
            website_url="https://google.com", request_id="12315aianodwdian"
        )
        assert isinstance(result, dict)
        assert {
            "website_url",
            "raw_document",
            "chunked_documents",
            "progress_status",
            "run_metadata",
            "pipeline_metadata",
            "chunk_metadata_list",
        } == set(result.keys())

    def test_get_chunking_called(self, indexing_service: IndexingService):
        _ = indexing_service.ingest_website(
            website_url="https://google.com", request_id="12315aianodwdian"
        )
        indexing_service.chunker_service.get.assert_called_once_with(
            chunker_name="hybrid", max_tokens=1021
        )
