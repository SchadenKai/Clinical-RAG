import json
from unittest.mock import AsyncMock

import pytest
from docling_core.transforms.chunker.doc_chunk import DocChunk
from docling_core.types.doc.document import DoclingDocument
from pymilvus import MilvusClient
from pytest_mock import MockerFixture, MockType

from app.agent.indexing.context import AgentContext
from app.agent.indexing.models import ProgressStatusEnum
from app.agent.indexing.nodes import (
    chunker_node,
    derive_source,
    doc_builder_node,
    file_ingestion_node,
    indexing_node,
    metadata_builder_node,
    web_scrapper,
)
from app.agent.indexing.state import AgentState
from app.core.config import Settings
from app.rag.chunker import ChunkerService


def _make_runtime(
    mocker: MockerFixture,
    *,
    milvus_db_name: str = "test_db",
    milvus_collection_name: str = "test_col",
    timezone: str = "UTC",
):
    mk_settings: MockType = mocker.Mock(spec=Settings)
    mk_settings.milvus_db_name = milvus_db_name
    mk_settings.milvus_collection_name = milvus_collection_name
    mk_settings.timezone = timezone

    mk_db_client: MockType = mocker.Mock(spec=MilvusClient)
    mk_db_client.query.return_value = []  # no duplicates by default

    mk_context: MockType = mocker.Mock(spec=AgentContext)
    mk_context.settings = mk_settings
    mk_context.db_client = mk_db_client
    # Explicitly set optional attributes
    # so spec-enforced mocks don't raise AttributeError
    mk_context.chunker = mocker.MagicMock()
    mk_context.embedding = mocker.MagicMock()
    mk_context.tokenizer = mocker.MagicMock()
    mk_context.s3_service = mocker.MagicMock()

    runtime = mocker.MagicMock()
    runtime.context = mk_context
    return runtime, mk_db_client


class TestWebScrapper:
    def test_web_scrapper_builds_docling_document(self, mocker: MockerFixture):
        fake_result = json.dumps(
            [
                {
                    "title": "Test Title",
                    "page_content": "Some body text here",
                    "date": "2024-01-01",
                    "tags": [{"name": "fever"}],
                }
            ]
        )
        mock_crawl_result = mocker.Mock()
        mock_crawl_result.extracted_content = fake_result

        mocker.patch(
            "app.agent.indexing.nodes.structured_output_scrapper",
            new=AsyncMock(return_value=mock_crawl_result),
        )

        state = AgentState(website_url="https://who.int/test")
        result = web_scrapper(state)

        doc = result["raw_document"]
        assert isinstance(doc, DoclingDocument)
        assert str(doc.origin.uri) == "https://who.int/test"
        assert result["pipeline_metadata"]["page_title"] == "Test Title"
        assert result["pipeline_metadata"]["source_type"] == "web"
        assert result["pipeline_metadata"]["tags"] == ["fever"]
        # Verify heading was added (document has items)
        assert len(list(doc.iterate_items())) >= 1

    def test_web_scrapper_empty_content(self, mocker: MockerFixture):
        fake_result = json.dumps([{"title": "Empty Page", "page_content": ""}])
        mock_crawl_result = mocker.Mock()
        mock_crawl_result.extracted_content = fake_result

        mocker.patch(
            "app.agent.indexing.nodes.structured_output_scrapper",
            new=AsyncMock(return_value=mock_crawl_result),
        )

        state = AgentState(website_url="https://cdc.gov/empty")
        result = web_scrapper(state)  # must not raise

        assert result["raw_document"] is not None
        assert result["pipeline_metadata"]["page_title"] == "Empty Page"


class TestFileIngestionNode:
    def test_file_ingestion_node_returns_expected_state(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)
        runtime.context.s3_service = mocker.Mock()
        runtime.context.settings.minio_bucket_name = "test-bucket"
        runtime.context.settings.minio_endpoint_url = "http://localhost:9000"

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        fake_doc.name = "test_doc"

        mock_converter = mocker.patch(
            "app.agent.indexing.nodes.doc_converter", return_value=fake_doc
        )

        fake_path = "/tmp/fake_file.pdf"
        mock_stager = mocker.MagicMock()
        mock_stager.__enter__ = mocker.Mock(return_value=fake_path)
        mock_stager.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("app.agent.indexing.nodes.S3FileStager", return_value=mock_stager)

        state = AgentState(file_key="uploads/test.pdf")
        result = file_ingestion_node(state, runtime)

        mock_converter.assert_called_once_with(fake_path)
        assert result["raw_document"] is fake_doc
        assert result["pipeline_metadata"]["source"] == "uploads/test.pdf"
        assert result["pipeline_metadata"]["source_type"] == "file"
        assert result["pipeline_metadata"]["page_title"] == "test_doc"
        assert result["progress_status"] == ProgressStatusEnum.LOADING_FILE


class TestChunkerNode:
    def test_chunker_node_calls_chunk_method(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_chunk: MockType = mocker.Mock(spec=DocChunk)
        fake_chunk.text = "chunk text"
        runtime.context.chunker.chunk.return_value = iter([fake_chunk])

        real_doc = DoclingDocument(name="test")
        state = AgentState.model_construct(raw_document=real_doc)

        result = chunker_node(state, runtime)

        runtime.context.chunker.chunk.assert_called_once_with(real_doc)
        assert result["chunked_documents"] == [fake_chunk]
        assert result["progress_status"] == ProgressStatusEnum.CHUNKING

    def test_chunker_node_returns_state_when_chunker_is_none(
        self, mocker: MockerFixture
    ):
        runtime, _ = _make_runtime(mocker)
        runtime.context.chunker = None

        real_doc = DoclingDocument(name="test")
        state = AgentState.model_construct(raw_document=real_doc)

        result = chunker_node(state, runtime)

        assert result is state

    def test_chunker_node_returns_state_when_raw_document_is_none(
        self, mocker: MockerFixture
    ):
        runtime, _ = _make_runtime(mocker)

        state = AgentState(raw_document=None)

        result = chunker_node(state, runtime)

        assert result is state


class TestMetadataBuilderNode:
    def test_metadata_builder_deduplication_produces_contiguous_indices(
        self, mocker: MockerFixture
    ):
        runtime, mk_db_client = _make_runtime(mocker, timezone="UTC")

        # Make the second chunk a duplicate by controlling hash_text output
        call_count = {"n": 0}

        def patched_hash(text: str) -> str:
            call_count["n"] += 1
            if call_count["n"] == 2:
                return "duplicate_hash_value"
            return f"unique_hash_{call_count['n']}"

        mocker.patch("app.agent.indexing.nodes.hash_text", side_effect=patched_hash)

        def query_side_effect(filter, **kwargs):
            if "duplicate_hash_value" in filter:
                return [{"id": "existing"}]
            return []

        mk_db_client.query.side_effect = query_side_effect

        def make_chunk(text: str) -> MockType:
            chunk = mocker.Mock(spec=DocChunk)
            chunk.text = text
            chunk.meta = mocker.Mock()
            chunk.meta.origin = None
            chunk.meta.headings = ["Heading"]
            return chunk

        chunks = [
            make_chunk("chunk 0"),
            make_chunk("chunk 1 dup"),
            make_chunk("chunk 2"),
        ]

        state = AgentState(
            chunked_documents=chunks,
            website_url="https://who.int/test",
        )
        result = metadata_builder_node(state, runtime)

        assert len(result.chunked_documents) == 2
        indices = [m["chunk_index"] for m in result.chunk_metadata_list]
        assert indices == [0, 1]  # contiguous, not [0, 2]

        # prev_chunk_id and next_chunk_id must also use deduped positions
        prev_ids = [m["prev_chunk_id"] for m in result.chunk_metadata_list]
        next_ids = [m["next_chunk_id"] for m in result.chunk_metadata_list]
        assert prev_ids == [0, 0]  # chunk 0: sentinel 0, chunk 1: prev deduped idx 0
        assert next_ids == [1, 2]  # chunk 0: next slot=1, chunk 1: next slot=2

    def test_metadata_builder_chunk_meta_none_guard(self, mocker: MockerFixture):
        runtime, mk_db_client = _make_runtime(mocker, timezone="UTC")
        mk_db_client.query.return_value = []

        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.text = "some text"
        chunk.meta = None  # simulate None meta

        state = AgentState(
            chunked_documents=[chunk],
            website_url="https://cdc.gov/test",
        )
        result = metadata_builder_node(state, runtime)

        assert result.chunk_metadata_list[0]["headings"] == []

    def test_metadata_builder_empty_list_returns_state(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker, timezone="UTC")

        state = AgentState(chunked_documents=[], website_url="https://who.int/test")
        result = metadata_builder_node(state, runtime)

        # Should return unchanged state and not call db_client
        assert result is state
        runtime.context.db_client.use_database.assert_not_called()

    def test_use_database_called_once_not_per_chunk(self, mocker: MockerFixture):
        runtime, mk_db_client = _make_runtime(mocker, timezone="UTC")
        mk_db_client.query.return_value = []

        def make_chunk(text: str) -> MockType:
            chunk = mocker.Mock(spec=DocChunk)
            chunk.text = text
            chunk.meta = mocker.Mock()
            chunk.meta.origin = None
            chunk.meta.headings = []
            return chunk

        state = AgentState(
            chunked_documents=[make_chunk(f"chunk {i}") for i in range(3)],
            website_url="https://who.int/test",
        )
        metadata_builder_node(state, runtime)

        # use_database must be called exactly once, not once per chunk
        mk_db_client.use_database.assert_called_once()


class TestDocBuilderNode:
    def test_doc_builder_final_documents_are_dicts(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_embedding_result: MockType = mocker.Mock()
        fake_embedding_result.embedding = [[0.1, 0.2, 0.3]]
        fake_embedding_result.model_dump.return_value = {
            "embedding": [[0.1, 0.2, 0.3]],
            "token_count": 5,
        }
        runtime.context.embedding.embed_documents.return_value = fake_embedding_result

        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.text = "test chunk"

        state = AgentState(
            chunked_documents=[chunk],
            chunk_metadata_list=[{"source": "https://who.int/doc", "chunk_index": 0}],
        )
        result = doc_builder_node(state, runtime)

        docs = result["final_documents"]
        assert isinstance(docs, list)
        assert all(isinstance(d, dict) for d in docs)
        assert docs[0]["text"] == "test chunk"
        assert "vector" in docs[0]

    def test_doc_builder_reuses_cleaned_text_from_metadata(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_embedding_result: MockType = mocker.Mock()
        fake_embedding_result.embedding = [[0.1, 0.2]]
        fake_embedding_result.model_dump.return_value = {
            "embedding": [[0.1, 0.2]],
            "token_count": 3,
        }
        runtime.context.embedding.embed_documents.return_value = fake_embedding_result

        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.text = "  raw  text  "

        state = AgentState(
            chunked_documents=[chunk],
            chunk_metadata_list=[
                {
                    "source": "https://who.int/doc",
                    "chunk_index": 0,
                    "cleaned_text": "pre-cleaned text",
                }
            ],
        )
        result = doc_builder_node(state, runtime)

        # The cleaned_text stored in metadata should be used, not re-cleaned raw text
        assert result["final_documents"][0]["text"] == "pre-cleaned text"


class TestIndexingNode:
    def test_indexing_node_inserts_documents_and_sets_done(self, mocker: MockerFixture):
        runtime, mk_db_client = _make_runtime(mocker)

        docs = [
            {"text": "doc 1", "vector": [0.1, 0.2], "source": "https://who.int/a"},
            {"text": "doc 2", "vector": [0.3, 0.4], "source": "https://who.int/b"},
        ]
        state = AgentState(final_documents=docs)

        result = indexing_node(state, runtime)

        mk_db_client.insert.assert_called_once_with(
            collection_name="test_col", data=docs
        )
        assert result.progress_status == ProgressStatusEnum.DONE

    def test_indexing_node_returns_state_when_final_documents_is_none(
        self, mocker: MockerFixture
    ):
        runtime, mk_db_client = _make_runtime(mocker)
        state = AgentState(final_documents=None)

        result = indexing_node(state, runtime)

        mk_db_client.insert.assert_not_called()
        assert result is state


class TestDeriveSource:
    def test_derive_source_fallback(self, mocker: MockerFixture):
        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.meta = mocker.Mock()
        chunk.meta.origin = None

        result = derive_source(chunk, {"source": "https://fallback.example.com"})
        assert result == "https://fallback.example.com"

    def test_derive_source_uses_uri_when_present(self, mocker: MockerFixture):
        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.meta = mocker.Mock()
        chunk.meta.origin = mocker.Mock()
        chunk.meta.origin.uri = "https://who.int/actual-source"
        chunk.meta.origin.filename = "ignored.pdf"

        result = derive_source(chunk, {"source": "https://fallback.com"})
        assert result == "https://who.int/actual-source"


class TestChunkerService:
    def test_chunker_service_unknown_name_raises(self):
        service = ChunkerService()
        with pytest.raises(ValueError, match="not available"):
            service.get("unknown")  # type: ignore[arg-type]
