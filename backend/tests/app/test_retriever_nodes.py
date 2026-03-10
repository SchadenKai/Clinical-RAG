from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pymilvus import MilvusClient

from app.agent.retriever.context import AgentContext
from app.agent.retriever.models import QueryGeneratorSOModel
from app.agent.retriever.nodes import embed_query, generate_queries, search
from app.agent.retriever.state import AgentState
from app.core.config import Settings


def _make_runtime(mocker, *, search_limit=3, rrf_k=60, search_score_threshold=0.01):
    mk_settings = mocker.Mock(spec=Settings)
    mk_settings.milvus_collection_name = "test_collection"
    mk_settings.milvus_db_name = "test_db"
    mk_settings.search_limit = search_limit
    mk_settings.rrf_k = rrf_k
    mk_settings.search_score_threshold = search_score_threshold
    mk_settings.reranker_top_k = 3

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
            embedded_query=[[0.1, 0.2, 0.3]],
            run_metadata={},
        )

        search(state, runtime)

        mk_db_client.hybrid_search.assert_called_once()
        call_kwargs = mk_db_client.hybrid_search.call_args

        assert call_kwargs.kwargs["collection_name"] == "test_collection"
        assert call_kwargs.kwargs["limit"] == 9  # reranker_top_k (3) * 3
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

    def test_search_multi_query_passes_all_embeddings_to_dense_req(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        multi_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        state = AgentState(
            input_query="malaria prevention",
            generated_queries=["malaria prevention", "malaria prophylaxis"],
            embedded_query=multi_embeddings,
            run_metadata={},
        )

        search(state, runtime)

        call_kwargs = mk_db_client.hybrid_search.call_args.kwargs
        dense_req = call_kwargs["reqs"][0]
        assert dense_req.data == multi_embeddings

    def test_search_multi_query_passes_all_text_to_sparse_req(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        text_queries = ["malaria prevention", "malaria prophylaxis"]
        state = AgentState(
            input_query="malaria prevention",
            generated_queries=text_queries,
            embedded_query=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            run_metadata={},
        )

        search(state, runtime)

        call_kwargs = mk_db_client.hybrid_search.call_args.kwargs
        sparse_req = call_kwargs["reqs"][1]
        assert sparse_req.data == text_queries

    def test_search_single_query_fallback_uses_input_query_for_sparse(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker)
        mk_db_client.hybrid_search.return_value = [[]]

        state = AgentState(
            input_query="fever treatment",
            generated_queries=None,
            embedded_query=[[0.1, 0.2, 0.3]],
            run_metadata={},
        )

        search(state, runtime)

        call_kwargs = mk_db_client.hybrid_search.call_args.kwargs
        sparse_req = call_kwargs["reqs"][1]
        assert sparse_req.data == ["fever treatment"]

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

    def test_search_multi_query_merges_and_deduplicates_result_groups(self, mocker):
        runtime, mk_db_client = _make_runtime(mocker, search_score_threshold=0.01)

        hit1 = _make_hit("doc1 text", "https://cdc.gov/1", "fever", 0.05, 101)
        hit2 = _make_hit("doc2 text", "https://who.int/2", "malaria", 0.04, 102)
        hit3_low = _make_hit("doc3 text", "https://cdc.gov/3", "dengue", 0.03, 103)
        hit3_high = _make_hit("doc3 text", "https://cdc.gov/3", "dengue", 0.07, 103)
        mk_db_client.hybrid_search.return_value = [[hit1, hit3_low], [hit2, hit3_high]]

        state = AgentState(
            input_query="malaria and dengue prevention",
            generated_queries=["malaria prevention", "dengue prevention"],
            embedded_query=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            run_metadata={},
        )

        new_state = search(state, runtime)

        assert len(new_state.documents) == 3
        result_ids = {doc["id"] for doc in new_state.documents}
        assert result_ids == {101, 102, 103}
        doc103 = next(doc for doc in new_state.documents if doc["id"] == 103)
        assert doc103["score"] == 0.07

    def test_search_multi_query_empty_group_still_returns_other_group_results(
        self, mocker
    ):
        runtime, mk_db_client = _make_runtime(mocker, search_score_threshold=0.01)

        hit1 = _make_hit("doc1 text", "https://cdc.gov/1", "fever", 0.05, 101)
        mk_db_client.hybrid_search.return_value = [[], [hit1]]

        state = AgentState(
            input_query="malaria prevention",
            generated_queries=["malaria prevention", "malaria prophylaxis"],
            embedded_query=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            run_metadata={},
        )

        new_state = search(state, runtime)

        assert len(new_state.documents) == 1
        assert new_state.documents[0]["id"] == 101


def _make_embedding_response(
    mocker, embedding, token_count=10, total_cost=0.001, duration_ms=50.0
):
    res = mocker.MagicMock()
    res.embedding = embedding
    res.token_count = token_count
    res.total_cost = total_cost
    res.duration_ms = duration_ms
    return res


def _make_queries_runtime(mocker, queries: list[str]):
    mk_chat_model = mocker.MagicMock()
    structured_model = mocker.MagicMock()
    structured_model.invoke.return_value = QueryGeneratorSOModel(queries=queries)
    mk_chat_model.with_structured_output.return_value = structured_model

    mk_context = mocker.MagicMock()
    mk_context.chat_model = mk_chat_model

    runtime = mocker.MagicMock()
    runtime.context = mk_context
    return runtime


class TestGenerateQueriesNode:
    def test_generate_queries_simple_query(self, mocker):
        runtime = _make_queries_runtime(mocker, queries=["what is malaria"])
        state = AgentState(input_query="what is malaria")

        new_state = generate_queries(state, runtime)

        assert new_state.generated_queries == ["what is malaria"]

    def test_generate_queries_complex_query(self, mocker):
        queries = [
            "malaria treatment protocols pediatric patients",
            "dengue fever treatment children",
            "comparison malaria dengue treatment guidelines",
        ]
        runtime = _make_queries_runtime(mocker, queries=queries)
        long_query = (
            "compare treatment protocols for malaria and dengue fever"
            " in pediatric patients"
        )
        state = AgentState(input_query=long_query)

        new_state = generate_queries(state, runtime)

        assert len(new_state.generated_queries) == 3
        assert new_state.generated_queries == queries

    def test_generate_queries_missing_input_raises(self, mocker):
        runtime = _make_queries_runtime(mocker, queries=["fallback"])
        with pytest.raises(ValidationError):
            generate_queries(AgentState(input_query=None), runtime)  # type: ignore[arg-type]

    def test_generate_queries_llm_failure_falls_back_to_input_query(self, mocker):
        runtime = _make_queries_runtime(mocker, queries=["unused"])
        structured_model = (
            runtime.context.chat_model.with_structured_output.return_value
        )
        structured_model.invoke.side_effect = RuntimeError("API error")

        state = AgentState(input_query="fever in children")

        new_state = generate_queries(state, runtime)

        assert new_state.generated_queries == ["fever in children"]

    def test_generate_queries_chat_model_none_raises(self, mocker):
        runtime = mocker.MagicMock()
        runtime.context.chat_model = None

        state = AgentState(input_query="malaria treatment")

        with pytest.raises(ValueError):
            generate_queries(state, runtime)

    def test_generate_queries_empty_queries_list_falls_back_to_input_query(
        self, mocker
    ):
        # QueryGeneratorSOModel(queries=[]) raises ValidationError (min_length=1).
        # The except block catches this and falls back to returning the original
        # input_query.
        def _raise_validation_error(*args, **kwargs):
            QueryGeneratorSOModel(queries=[])

        runtime = _make_queries_runtime(mocker, queries=["unused"])
        structured_model = (
            runtime.context.chat_model.with_structured_output.return_value
        )
        structured_model.invoke.side_effect = _raise_validation_error

        state = AgentState(input_query="fever in children")

        new_state = generate_queries(state, runtime)

        assert new_state.generated_queries == ["fever in children"]


class TestQueryGeneratorSOModel:
    def test_empty_queries_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QueryGeneratorSOModel(queries=[])


class TestEmbedQueryNode:
    def _make_runtime(self, mocker, embedding_side_effect=None):
        mk_embedding = mocker.MagicMock()
        if embedding_side_effect:
            mk_embedding.embed_query.side_effect = embedding_side_effect

        mk_tokenizer = mocker.MagicMock()

        mk_context = mocker.MagicMock()
        mk_context.embedding = mk_embedding
        mk_context.tokenizer = mk_tokenizer

        runtime = mocker.MagicMock()
        runtime.context = mk_context
        return runtime, mk_embedding

    def test_embed_query_uses_generated_queries(self, mocker):
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.4, 0.5, 0.6]
        responses = [
            _make_embedding_response(mocker, vec1),
            _make_embedding_response(mocker, vec2),
        ]
        runtime, mk_embedding = self._make_runtime(
            mocker, embedding_side_effect=responses
        )

        state = AgentState(
            input_query="malaria prevention",
            generated_queries=["malaria prevention", "malaria prophylaxis"],
        )

        new_state = embed_query(state, runtime)

        assert mk_embedding.embed_query.call_count == 2
        assert new_state.embedded_query == [vec1, vec2]

    def test_embed_query_fallback_to_input_query(self, mocker):
        vec = [0.1, 0.2, 0.3]
        runtime, mk_embedding = self._make_runtime(
            mocker, embedding_side_effect=[_make_embedding_response(mocker, vec)]
        )

        state = AgentState(
            input_query="fever treatment",
            generated_queries=None,
        )

        new_state = embed_query(state, runtime)

        mk_embedding.embed_query.assert_called_once()
        call_args = mk_embedding.embed_query.call_args
        assert call_args.kwargs["text"] == "fever treatment"
        assert new_state.embedded_query == [vec]

    def test_embed_query_empty_generated_queries_falls_back_to_input_query(
        self, mocker
    ):
        vec = [0.1, 0.2, 0.3]
        runtime, mk_embedding = self._make_runtime(
            mocker, embedding_side_effect=[_make_embedding_response(mocker, vec)]
        )

        state = AgentState(
            input_query="fever treatment",
            generated_queries=[],
        )

        new_state = embed_query(state, runtime)

        mk_embedding.embed_query.assert_called_once()
        call_args = mk_embedding.embed_query.call_args
        assert call_args.kwargs["text"] == "fever treatment"
        assert new_state.embedded_query == [vec]

    def test_embed_query_aggregates_metadata(self, mocker):
        responses = [
            _make_embedding_response(
                mocker, [0.1], token_count=5, total_cost=0.001, duration_ms=20.0
            ),
            _make_embedding_response(
                mocker, [0.2], token_count=7, total_cost=0.002, duration_ms=30.0
            ),
        ]
        runtime, _ = self._make_runtime(mocker, embedding_side_effect=responses)

        state = AgentState(
            input_query="q",
            generated_queries=["query one", "query two"],
        )

        new_state = embed_query(state, runtime)

        assert new_state.run_metadata["token_count"] == 12
        assert abs(new_state.run_metadata["total_cost"] - 0.003) < 1e-9
        assert abs(new_state.run_metadata["duration_ms"] - 50.0) < 1e-9
