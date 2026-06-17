"""Tests for the metadata_builder_node in app/agent/indexing/nodes.py."""

import datetime

import pytest
from pymilvus import MilvusClient

from app.agent.indexing.context import AgentContext
from app.agent.indexing.models import SourceClass
from app.agent.indexing.nodes import metadata_builder_node
from app.agent.indexing.state import AgentState
from app.core.config import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(text: str, meta: dict | None = None):
    """Return a minimal mock that quacks like a docling BaseChunk."""
    import unittest.mock as mock

    chunk = mock.MagicMock()
    chunk.text = text
    chunk.meta = meta if meta is not None else {}
    return chunk


def _make_runtime(mocker, *, timezone: str = "UTC", no_duplicates: bool = True):
    """Build a fully-wired mock runtime[AgentContext]."""
    mk_settings = mocker.Mock(spec=Settings)
    mk_settings.timezone = timezone
    mk_settings.milvus_db_name = "test_db"
    mk_settings.milvus_collection_name = "test_collection"

    mk_db_client = mocker.Mock(spec=MilvusClient)
    # By default the DB says "no duplicate found"
    mk_db_client.query.return_value = [] if no_duplicates else [{"id": "abc"}]

    mk_context = mocker.Mock(spec=AgentContext)
    mk_context.settings = mk_settings
    mk_context.db_client = mk_db_client

    runtime = mocker.MagicMock()
    runtime.context = mk_context

    return runtime, mk_db_client


def _state_with_chunks(chunks: list, website_url: str | None = "https://who.int/guideline") -> AgentState:
    """Create an AgentState with chunked_documents set to an iterator over the given list."""
    return AgentState(
        website_url=website_url,
        chunked_documents=iter(chunks),
    )


# ---------------------------------------------------------------------------
# Guard-clause tests
# ---------------------------------------------------------------------------


class TestMetadataBuilderNodeGuards:
    def test_returns_state_unchanged_when_chunked_documents_is_none(self, mocker):
        """Node must short-circuit and return the original state when there are no chunks."""
        runtime, _ = _make_runtime(mocker)
        state = AgentState(website_url="https://who.int/guideline")
        # chunked_documents defaults to None

        result = metadata_builder_node(state, runtime)

        assert result is state  # exact same object returned

    def test_returns_state_unchanged_when_settings_is_none(self, mocker):
        """Node must short-circuit when runtime.context.settings is None."""
        runtime, _ = _make_runtime(mocker)
        runtime.context.settings = None

        chunk = _make_chunk("Some text")
        state = _state_with_chunks([chunk])

        result = metadata_builder_node(state, runtime)

        assert result is state


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestMetadataBuilderNodeHappyPath:
    def test_returns_new_state_object(self, mocker):
        """Node must return a model_copy (not the same object)."""
        runtime, _ = _make_runtime(mocker)
        chunk = _make_chunk("Hello world")
        state = _state_with_chunks([chunk])

        result = metadata_builder_node(state, runtime)

        assert result is not state

    def test_result_contains_processed_chunks(self, mocker):
        """The returned state must expose the surviving chunks."""
        runtime, _ = _make_runtime(mocker)
        chunk = _make_chunk("Hello world")
        state = _state_with_chunks([chunk])

        result = metadata_builder_node(state, runtime)

        assert result.chunked_documents is not None
        assert len(result.chunked_documents) == 1

    def test_cleans_whitespace_in_chunk_text(self, mocker):
        """clean_chunk_content should collapse internal whitespace in-place on the chunk."""
        runtime, _ = _make_runtime(mocker)
        chunk = _make_chunk("Hello   \n  world")
        state = _state_with_chunks([chunk], website_url="https://cdc.gov/guideline")

        metadata_builder_node(state, runtime)

        assert chunk.text == "Hello world"

    def test_content_hash_is_set(self, mocker):
        """Each chunk must receive a sha256 content_hash in its meta dict."""
        runtime, _ = _make_runtime(mocker)
        chunk = _make_chunk("Some important content")
        state = _state_with_chunks([chunk])

        metadata_builder_node(state, runtime)

        assert "content_hash" in chunk.meta
        # SHA-256 hex digest is always 64 characters
        assert len(chunk.meta["content_hash"]) == 64

    def test_chunk_index_metadata_set_correctly(self, mocker):
        """chunk_index, prev_chunk_id, and next_chunk_id must be set per chunk."""
        runtime, _ = _make_runtime(mocker)
        chunks = [_make_chunk(f"Chunk {i}") for i in range(3)]
        state = _state_with_chunks(chunks)

        result = metadata_builder_node(state, runtime)

        docs = result.chunked_documents
        assert docs[0].meta["chunk_index"] == 0
        assert docs[0].meta["prev_chunk_id"] == 0  # first chunk: prev = 0
        assert docs[0].meta["next_chunk_id"] == 1

        assert docs[1].meta["chunk_index"] == 1
        assert docs[1].meta["prev_chunk_id"] == 0
        assert docs[1].meta["next_chunk_id"] == 2

        assert docs[2].meta["chunk_index"] == 2
        assert docs[2].meta["prev_chunk_id"] == 1
        assert docs[2].meta["next_chunk_id"] == 3  # last chunk: next = len(list)

    def test_last_updated_is_timezone_aware_iso_format(self, mocker):
        """last_updated must be a valid, timezone-aware ISO-8601 datetime string."""
        runtime, _ = _make_runtime(mocker, timezone="UTC")
        chunk = _make_chunk("Text")
        state = _state_with_chunks([chunk], website_url="https://cdc.gov/guideline")

        metadata_builder_node(state, runtime)

        last_updated = chunk.meta["last_updated"]
        parsed = datetime.datetime.fromisoformat(last_updated)
        assert parsed.tzinfo is not None  # must be timezone-aware

    @pytest.mark.parametrize(
        "url, expected_source_class",
        [
            ("https://who.int/some-guideline", SourceClass.WHO.value),
            ("https://cdc.gov/some-guideline", SourceClass.CDC.value),
            ("https://example.com/other", SourceClass.OTHERS.value),
            (None, SourceClass.OTHERS.value),
        ],
    )
    def test_source_class_assigned_by_url(self, mocker, url, expected_source_class):
        """source_class must reflect the correct origin based on the website URL."""
        runtime, _ = _make_runtime(mocker)
        chunk = _make_chunk("Guideline text")
        state = _state_with_chunks([chunk], website_url=url)

        metadata_builder_node(state, runtime)

        assert chunk.meta["source_class"] == expected_source_class

    def test_use_database_called_for_each_chunk(self, mocker):
        """use_database() must be called once for every chunk processed."""
        runtime, mk_db_client = _make_runtime(mocker)
        chunks = [_make_chunk(f"Chunk {i}") for i in range(4)]
        state = _state_with_chunks(chunks)

        metadata_builder_node(state, runtime)

        assert mk_db_client.use_database.call_count == 4
        mk_db_client.use_database.assert_called_with("test_db")

    def test_duplicate_check_query_uses_content_hash(self, mocker):
        """The Milvus query for duplicate detection must filter on content_hash."""
        runtime, mk_db_client = _make_runtime(mocker)
        chunk = _make_chunk("Unique text")
        state = _state_with_chunks([chunk])

        metadata_builder_node(state, runtime)

        mk_db_client.query.assert_called_once()
        call_kwargs = mk_db_client.query.call_args
        assert "content_hash" in call_kwargs.kwargs["filter"]
        assert call_kwargs.kwargs["collection_name"] == "test_collection"
        assert "id" in call_kwargs.kwargs["output_fields"]


# ---------------------------------------------------------------------------
# Duplicate filtering tests
# ---------------------------------------------------------------------------


class TestMetadataBuilderNodeDuplicates:
    def test_duplicate_chunks_are_excluded_from_result(self, mocker):
        """Chunks whose content_hash already exists in Milvus must be dropped."""
        runtime, mk_db_client = _make_runtime(mocker)
        # First chunk is a duplicate, second is unique
        mk_db_client.query.side_effect = [
            [{"id": "existing"}],  # duplicate for chunk 0
            [],  # no duplicate for chunk 1
        ]
        chunks = [_make_chunk("Duplicate text"), _make_chunk("Unique text")]
        state = _state_with_chunks(chunks)

        result = metadata_builder_node(state, runtime)

        assert len(result.chunked_documents) == 1
        assert result.chunked_documents[0].text == "Unique text"

    def test_all_duplicates_returns_empty_list(self, mocker):
        """If every chunk is a duplicate the result list must be empty."""
        runtime, mk_db_client = _make_runtime(mocker, no_duplicates=False)
        chunks = [_make_chunk(f"Dup {i}") for i in range(3)]
        state = _state_with_chunks(chunks)

        result = metadata_builder_node(state, runtime)

        assert result.chunked_documents == []

    def test_no_duplicates_keeps_all_chunks(self, mocker):
        """When no duplicates exist, all chunks must survive into the result."""
        runtime, _ = _make_runtime(mocker, no_duplicates=True)
        chunks = [_make_chunk(f"Unique chunk {i}") for i in range(5)]
        state = _state_with_chunks(chunks)

        result = metadata_builder_node(state, runtime)

        assert len(result.chunked_documents) == 5

    def test_metadata_not_set_on_duplicate_chunks(self, mocker):
        """chunk_index and last_updated must NOT be stamped on a duplicate chunk."""
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.query.return_value = [{"id": "dup"}]  # always a duplicate

        chunk = _make_chunk("Duplicate")
        state = _state_with_chunks([chunk])

        metadata_builder_node(state, runtime)

        assert "chunk_index" not in chunk.meta
        assert "last_updated" not in chunk.meta
