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
    _derive_source,
    chunker_node,
    doc_builder_node,
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


class TestChunkerNode:
    def test_chunker_node_calls_chunk_method(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_chunk: MockType = mocker.Mock(spec=DocChunk)
        fake_chunk.text = "chunk text"
        runtime.context.chunker.chunk.return_value = iter([fake_chunk])

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        state = AgentState(raw_document=fake_doc)

        result = chunker_node(state, runtime)

        runtime.context.chunker.chunk.assert_called_once_with(fake_doc)
        assert result["chunked_documents"] == [fake_chunk]
        assert result["progress_status"] == ProgressStatusEnum.CHUNKING


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

        chunks = [make_chunk("chunk 0"), make_chunk("chunk 1 dup"), make_chunk("chunk 2")]

        state = AgentState(
            chunked_documents=chunks,
            website_url="https://who.int/test",
        )
        result = metadata_builder_node(state, runtime)

        assert len(result.chunked_documents) == 2
        indices = [m["chunk_index"] for m in result.chunk_metadata_list]
        assert indices == [0, 1]  # contiguous, not [0, 2]

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
        runtime.context.tokenizer = mocker.Mock()

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


class TestDeriveSource:
    def test_derive_source_fallback(self, mocker: MockerFixture):
        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.meta = mocker.Mock()
        chunk.meta.origin = None

        result = _derive_source(chunk, {"source": "https://fallback.example.com"})
        assert result == "https://fallback.example.com"

    def test_derive_source_uses_uri_when_present(self, mocker: MockerFixture):
        chunk: MockType = mocker.Mock(spec=DocChunk)
        chunk.meta = mocker.Mock()
        chunk.meta.origin = mocker.Mock()
        chunk.meta.origin.uri = "https://who.int/actual-source"
        chunk.meta.origin.filename = "ignored.pdf"

        result = _derive_source(chunk, {"source": "https://fallback.com"})
        assert result == "https://who.int/actual-source"


class TestChunkerService:
    def test_chunker_service_unknown_name_raises(self):
        service = ChunkerService()
        with pytest.raises(ValueError, match="not available"):
            service.get("unknown")  # type: ignore[arg-type]
