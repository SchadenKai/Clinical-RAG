from unittest.mock import MagicMock, patch

import pytest

from app.agent.retriever.nodes import rerank_node
from app.agent.retriever.state import AgentState
from app.services.reranking import RerankerService


@pytest.fixture
def sample_documents():
    return [
        {
            "id": "doc1",
            "text": "This is a completely irrelevant document.",
            "source": "source1",
        },
        {
            "id": "doc2",
            "text": "This document is highly relevant to the query.",
            "source": "source2",
        },
        {"id": "doc3", "text": "This is somewhat relevant.", "source": "source3"},
    ]


# ---------------------------------------------------------------------------
# Provider: SLM
# ---------------------------------------------------------------------------


@patch("sentence_transformers.CrossEncoder")
def test_reranker_service_slm(mock_cross_encoder, sample_documents):
    mock_model_instance = MagicMock()
    # Giving high score to doc2, medium to doc3, low to doc1
    mock_model_instance.predict.return_value = [1.0, 9.5, 5.0]
    mock_cross_encoder.return_value = mock_model_instance

    service = RerankerService(provider="slm", model_name="cross-encoder/dummy-model")

    reranked = service.rerank("relevant query", sample_documents, top_k=2)

    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc2"  # Highest score (9.5)
    assert reranked[1]["id"] == "doc3"  # Second highest (5.0)
    assert "rerank_score" in reranked[0]
    # Verify original documents are not mutated
    assert "rerank_score" not in sample_documents[0]


# ---------------------------------------------------------------------------
# Provider: LLM
# ---------------------------------------------------------------------------


def test_reranker_service_llm(sample_documents):
    mock_client = MagicMock()
    mock_structured_model = MagicMock()
    mock_client.with_structured_output.return_value = mock_structured_model

    scores = [1.0, 9.5, 5.0]
    call_count = {"count": 0}

    def side_effect_invoke(*args, **kwargs):
        class MockResponse:
            score = scores[call_count["count"]]

        call_count["count"] += 1
        return MockResponse()

    mock_structured_model.invoke.side_effect = side_effect_invoke

    mock_chat_service = MagicMock()
    mock_chat_service.client = mock_client

    service = RerankerService(
        provider="llm",
        model_name="gpt-4o",
        chat_model_service=mock_chat_service,
    )

    reranked = service.rerank("relevant query", sample_documents, top_k=2)

    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc2"  # Highest score
    assert reranked[1]["id"] == "doc3"  # Second highest
    assert reranked[0]["rerank_score"] == 9.5
    # Verify original documents are not mutated
    assert "rerank_score" not in sample_documents[0]


def test_rerank_llm_invoke_failure(sample_documents):
    """Documents whose LLM scoring raises should fall back to score 0.0."""
    mock_client = MagicMock()
    mock_structured_model = MagicMock()
    mock_client.with_structured_output.return_value = mock_structured_model
    mock_structured_model.invoke.side_effect = RuntimeError("LLM unavailable")

    mock_chat_service = MagicMock()
    mock_chat_service.client = mock_client

    service = RerankerService(
        provider="llm",
        model_name="gpt-4o",
        chat_model_service=mock_chat_service,
    )

    reranked = service.rerank("query", sample_documents, top_k=3)

    assert len(reranked) == 3
    for doc in reranked:
        assert doc["rerank_score"] == 0.0


def test_model_property_llm_raises():
    """Accessing .model on an LLM provider should raise AttributeError."""
    mock_chat_service = MagicMock()
    service = RerankerService(
        provider="llm",
        model_name="gpt-4o",
        chat_model_service=mock_chat_service,
    )
    with pytest.raises(AttributeError, match="'llm' provider"):
        _ = service.model


# ---------------------------------------------------------------------------
# Validation / _validate_provider
# ---------------------------------------------------------------------------


def test_validate_provider_invalid():
    """Unknown provider string should raise ValueError at init."""
    with pytest.raises(ValueError, match="Unknown reranker provider"):
        RerankerService(provider="unknown", model_name="dummy")


def test_validate_provider_llm_without_chat_service():
    """'llm' provider without chat_model_service should raise ValueError."""
    with pytest.raises(ValueError, match="requires chat_model_service"):
        RerankerService(provider="llm", model_name="gpt-4o")


def test_validate_provider_milvus_not_implemented():
    """'milvus:*' providers should raise ValueError (not yet implemented)."""
    with pytest.raises(ValueError, match="not yet implemented"):
        RerankerService(provider="milvus:weighted", model_name="dummy")


# ---------------------------------------------------------------------------
# Edge cases: rerank()
# ---------------------------------------------------------------------------


def test_rerank_empty_documents():
    """rerank() with an empty document list should return an empty list."""
    mock_chat_service = MagicMock()
    service = RerankerService(
        provider="llm",
        model_name="gpt-4o",
        chat_model_service=mock_chat_service,
    )
    result = service.rerank("query", [], top_k=5)
    assert result == []


@patch("sentence_transformers.CrossEncoder")
def test_rerank_top_k_exceeds_document_count(mock_cross_encoder, sample_documents):
    """top_k larger than the number of documents should return all documents."""
    mock_model_instance = MagicMock()
    mock_model_instance.predict.return_value = [1.0, 9.5, 5.0]
    mock_cross_encoder.return_value = mock_model_instance

    service = RerankerService(provider="slm", model_name="cross-encoder/dummy-model")

    # top_k=100 but only 3 documents
    reranked = service.rerank("query", sample_documents, top_k=100)

    assert len(reranked) == 3


# ---------------------------------------------------------------------------
# rerank_node (LangGraph node)
# ---------------------------------------------------------------------------


@patch("sentence_transformers.CrossEncoder")
def test_rerank_node(mock_cross_encoder, sample_documents):
    """rerank_node should update state.documents with reranked results."""
    mock_model_instance = MagicMock()
    mock_model_instance.predict.return_value = [1.0, 9.5, 5.0]
    mock_cross_encoder.return_value = mock_model_instance

    reranker = RerankerService(provider="slm", model_name="cross-encoder/dummy-model")

    mock_settings = MagicMock()
    mock_settings.reranker_top_k = 2

    mock_context = MagicMock()
    mock_context.reranker = reranker
    mock_context.settings = mock_settings

    mock_runtime = MagicMock()
    mock_runtime.context = mock_context

    state = AgentState(
        input_query="relevant query",
        documents=sample_documents,
        sources=["source1", "source2", "source3"],
    )

    updated_state = rerank_node(state, mock_runtime)

    assert len(updated_state.documents) == 2
    assert updated_state.documents[0]["id"] == "doc2"
    assert updated_state.documents[1]["id"] == "doc3"
    assert "rerank_duration_ms" in updated_state.run_metadata


def test_rerank_node_empty_documents():
    """rerank_node with no documents should return state unchanged."""
    mock_context = MagicMock()
    mock_runtime = MagicMock()
    mock_runtime.context = mock_context

    state = AgentState(input_query="query", documents=[])
    updated_state = rerank_node(state, mock_runtime)

    assert updated_state.documents == []
    # reranker should not be called
    mock_context.reranker.rerank.assert_not_called()
