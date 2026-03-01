"""
API integration tests for /vector_db endpoints.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _patched_stream():
    """Returns a mock iterable simulating the agent stream."""
    return iter(
        [
            {
                "react_loop_node": {
                    "messages": [MagicMock(content="Some clinical result.")]
                }
            }
        ]
    )


def _patched_search_ctx():
    return (
        patch("app.agent.chat.main.agent.stream", return_value=_patched_stream()),
        patch("app.agent.chat.context.AgentContext", return_value=MagicMock()),
    )


class TestVectorDBEndpoints:
    """Tests for POST /vector_db/search and DELETE /vector_db/collection."""

    # ── POST /vector_db/search ─────────────────────────────────────────────────

    def test_search_returns_result(self, client: TestClient):
        """POST /vector_db/search should return a 'result' key."""
        p1, p2 = _patched_search_ctx()
        with p1, p2:
            resp = client.post(
                "/v1/vector_db/search",
                json={"query": "COVID-19 treatment guidelines"},
            )

        assert resp.status_code == 200
        assert "result" in resp.json()

    def test_search_missing_body_returns_422(self, client: TestClient):
        """POST /vector_db/search without body should return 422."""
        resp = client.post("/v1/vector_db/search")
        assert resp.status_code == 422

    def test_search_different_query(self, client: TestClient):
        """Search should work regardless of query text."""
        stream_return = iter(
            [{"fast_node": {"messages": [MagicMock(content="Malaria info.")]}}]
        )
        with (
            patch("app.agent.chat.main.agent.stream", return_value=stream_return),
            patch("app.agent.chat.context.AgentContext", return_value=MagicMock()),
        ):
            resp = client.post(
                "/v1/vector_db/search",
                json={"query": "malaria prevention"},
            )

        assert resp.status_code == 200

    # ── DELETE /vector_db/collection ──────────────────────────────────────────

    def test_clear_collection(self, client: TestClient):
        """
        DELETE /vector_db/collection should return 200 with the 
        mock Milvus client.
        """
        resp = client.delete("/v1/vector_db/collection")
        assert resp.status_code in (200, 204)
