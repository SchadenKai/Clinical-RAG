import pytest
from unittest.mock import MagicMock, patch
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


@patch("app.services.reranking.service.CrossEncoder")
def test_reranker_service_slm(mock_cross_encoder, sample_documents):
    # Mock the predict method to return explicit scores
    mock_model_instance = MagicMock()
    # Giving high score to doc2, medium to doc3, low to doc1
    mock_model_instance.predict.return_value = [1.0, 9.5, 5.0]
    mock_cross_encoder.return_value = mock_model_instance

    service = RerankerService(
        provider="slm", model_name="dummy/model"
    )

    # Execution
    reranked = service.rerank("relevant query", sample_documents, top_k=2)

    # Assertions
    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc2"  # Highest score (9.5)
    assert reranked[1]["id"] == "doc3"  # Second highest (5.0)
    assert "rerank_score" in reranked[0]
    # Verify original documents are not mutated
    assert "rerank_score" not in sample_documents[0]


@patch("app.services.reranking.service.ChatModelService")
def test_reranker_service_llm(mock_chat_service_class, sample_documents):
    # Mock the chat service and structured output
    mock_client = MagicMock()
    mock_structured_model = MagicMock()
    mock_client.with_structured_output.return_value = mock_structured_model

    # We will simulate the LLM returning 3 different scores for the 3 docs
    # Side effect function to assign scores sequentially
    scores = [1.0, 9.5, 5.0]
    call_count = {"count": 0}

    def side_effect_invoke(*args, **kwargs):
        class MockResponse:
            score = scores[call_count["count"]]

        call_count["count"] += 1
        return MockResponse()

    mock_structured_model.invoke.side_effect = side_effect_invoke
    mock_chat_service_class.return_value.client = mock_client

    # Create a real mock ChatModelService to pass to RerankerService
    mock_chat_service = MagicMock()
    mock_chat_service.client = mock_client

    service = RerankerService(
        provider="llm",
        model_name="gpt-4o",
        chat_model_service=mock_chat_service,
    )

    # Execution
    reranked = service.rerank("relevant query", sample_documents, top_k=2)

    # Assertions
    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc2"  # Highest score
    assert reranked[1]["id"] == "doc3"  # Second highest
    assert reranked[0]["rerank_score"] == 9.5
    # Verify original documents are not mutated
    assert "rerank_score" not in sample_documents[0]
