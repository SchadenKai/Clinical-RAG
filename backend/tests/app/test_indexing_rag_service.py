import pytest
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter
from langgraph.graph.state import CompiledStateGraph
from pymilvus import MilvusClient
from pytest_mock import MockerFixture, MockType

from app.agent.indexing.models import RelevantDocs
from app.core.config import Settings
from app.rag.chunker import ChunkerService
from app.rag.db import VectorClient
from app.rag.embeddings import EmbeddingService
from app.services.llm.tokenizer import TokenizerService
from app.services.rag import IndexingService


class TestIndexingRAGService:
    @pytest.fixture
    def indexing_service(self, mocker: MockerFixture) -> IndexingService:
        fake_text_splitter: MockType = mocker.Mock(spec=TextSplitter)
        fake_vector_client: MockType = mocker.Mock(spec=MilvusClient)

        mk_chunker_service: MockType = mocker.Mock(spec=ChunkerService)
        mk_chunker_service.get.return_value = fake_text_splitter
        mk_embedding_service: MockType = mocker.Mock(spec=EmbeddingService)

        mk_vector_db_service: MockType = mocker.Mock(spec=VectorClient)
        mk_vector_db_service.client = fake_vector_client

        mk_tokenizer_service: MockType = mocker.Mock(spec=TokenizerService)

        mk_indexing_agent: MockType = mocker.Mock(spec=CompiledStateGraph)
        mk_indexing_agent.stream.return_value = [
            {
                "indexing_node": {
                    "website_url": "https://google.com",
                    "raw_document": [
                        Document(
                            page_content="testing 1",
                            metadata={"source": "https://google.com"},
                        ),
                        Document(
                            page_content="testing 2",
                            metadata={"source": "https://google.com"},
                        ),
                    ],
                    "chunked_documents": [
                        Document(
                            page_content="testing 1",
                            metadata={"source": "https://google.com"},
                        ),
                        Document(
                            page_content="testing 2",
                            metadata={"source": "https://google.com"},
                        ),
                    ],
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
                },
            }
        ]

        mk_settings: MockType = mocker.Mock(spec=Settings)
        mk_settings.milvus_collection_name = "collection_name"

        return IndexingService(
            chunker_service=mk_chunker_service,
            embedding_service=mk_embedding_service,
            indexing_agent=mk_indexing_agent,
            tokenizer_service=mk_tokenizer_service,
            vector_db_service=mk_vector_db_service,
            settings=mk_settings,
        )

    def test_ingestion_return_run_metadata_only(
        self, indexing_service: IndexingService
    ):
        result = indexing_service.ingest_document(
            website_url="https://google.com", request_id="12315aianodwdian"
        )
        assert isinstance(result, dict)
        assert {"token_count", "total_cost", "duration_ms", "event"}.issubset(
            result.keys()
        )

    def test_get_chunking_called(self, indexing_service: IndexingService):
        _ = indexing_service.ingest_document(
            website_url="https://google.com", request_id="12315aianodwdian"
        )
        indexing_service.chunker_service.get.assert_called_once_with(
            chunker_name="recursive", chunk_size=1021, chunk_overlap=10
        )
