from unittest.mock import MagicMock, patch

import pytest
from pymilvus import MilvusClient

from app.agent.retriever.context import AgentContext
from app.agent.retriever.nodes import search
from app.agent.retriever.state import AgentState
from app.core.config import Settings


def _make_runtime(mocker, *, search_limit=3, rrf_k=60, search_score_threshold=0.01):
    mk_settings = mocker.Mock(spec=Settings)
    mk_settings.milvus_collection_name = "test_collection"
    mk_settings.milvus_db_name = "test_db"
    mk_settings.search_limit = search_limit
    mk_settings.rrf_k = rrf_k
    mk_settings.search_score_threshold = search_score_threshold

    mk_db_client = mocker.Mock(spec=MilvusClient)

    mk_context = mocker.Mock(spec=AgentContext)
    mk_context.settings = mk_settings
    mk_context.db_client = mk_db_client

    runtime = mocker.MagicMock()
    runtime.context = mk_context

    return runtime, mk_db_client


def _make_hit(text, source, category, score, hit_id):
    hit = MagicMock()
    hit.entity = {"text": text, "source": source, "category": category}
    hit.distance = score
    hit.id = hit_id
    return hit


class TestSearchNode:
    def test_search_correct_params(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        state = AgentState(
            input_query="fever in children",
            embedded_query=[0.1, 0.2, 0.3],
            run_metadata={},
        )

        search(state, runtime)

        mk_db_client.hybrid_search.assert_called_once()
        call_kwargs = mk_db_client.hybrid_search.call_args

        assert call_kwargs.kwargs["collection_name"] == "test_collection"
        assert call_kwargs.kwargs["limit"] == 3
        assert call_kwargs.kwargs["output_fields"] == ["text", "category", "source"]

        reqs = call_kwargs.kwargs["reqs"]
        assert len(reqs) == 2
        dense_req, sparse_req = reqs
        assert dense_req.anns_field == "vector"
        assert sparse_req.anns_field == "sparse_vector"

    def test_search_result_parsing(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)

        hit1 = _make_hit("doc1 text", "https://cdc.gov/1", "fever", 0.05, 101)
        hit2 = _make_hit("doc2 text", "https://who.int/2", "malaria", 0.03, 102)
        mk_db_client.hybrid_search.return_value = [[hit1, hit2]]

        state = AgentState(
            input_query="fever treatment",
            embedded_query=[[0.1, 0.2, 0.3]],
            run_metadata={},
        )

        new_state = search(state, runtime)

        assert len(new_state.documents) == 2
        assert new_state.documents[0]["text"] == "doc1 text"
        assert new_state.documents[0]["score"] == 0.05
        assert new_state.documents[0]["id"] == 101
        assert new_state.sources == ["https://cdc.gov/1", "https://who.int/2"]

    def test_search_empty_results(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        state = AgentState(
            input_query="unknown topic",
            embedded_query=[[0.1, 0.2, 0.3]],
            run_metadata={},
        )

        new_state = search(state, runtime)

        assert new_state.documents == []
        assert new_state.sources == []

    def test_search_normalizes_flat_embedding(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        flat_embedding = [0.1, 0.2, 0.3]
        state = AgentState(
            input_query="malaria prevention",
            embedded_query=flat_embedding,
            run_metadata={},
        )

        search(state, runtime)

        call_kwargs = mk_db_client.hybrid_search.call_args.kwargs
        dense_req = call_kwargs["reqs"][0]
        # After normalization the embedding must be wrapped in an outer list
        assert isinstance(dense_req.data, list)
        assert isinstance(dense_req.data[0], list)

    def test_search_threshold_filters_low_score_results(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker, search_score_threshold=0.02)

        hit_above = _make_hit("good doc", "https://cdc.gov/1", "fever", 0.05, 1)
        hit_below = _make_hit("bad doc", "https://who.int/2", "other", 0.005, 2)
        mk_db_client.hybrid_search.return_value = [[hit_above, hit_below]]

        state = AgentState(
            input_query="fever",
            embedded_query=[[0.1, 0.2, 0.3]],
            run_metadata={},
        )

        new_state = search(state, runtime)

        assert len(new_state.documents) == 1
        assert new_state.documents[0]["score"] == 0.05
        assert new_state.sources == ["https://cdc.gov/1"]
