"""
API integration tests for /chat endpoints.
Uses in-memory SQLite DB, mocked LLM/graph via patching at the source.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db.models import ChatConversation, ChatMessage
from tests.api.conftest import _DEV_USER_ID, TestingSessionLocal


class TestChatEndpoints:
    """Tests for POST /chat and /chat/sessions CRUD."""

    # ── POST /chat ─────────────────────────────────────────────────────────────

    def test_chat_general_agent_returns_response(self, client: TestClient):
        """Basic chat call should return a 'response' key."""
        with patch(
            "app.services.chat.ChatService.send_message",
            return_value="Hello from the bot!",
        ):
            resp = client.post(
                "/v1/chat?agent_id=general",
                json={"query": "What is COVID-19?"},
            )

        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_with_session_id_reuses_session(self, client: TestClient):
        """Supplying an existing session_id should respond normally."""
        db = TestingSessionLocal()
        conv = ChatConversation(user_id=_DEV_USER_ID, title="Existing")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        session_id = conv.id
        db.close()

        with patch("app.services.chat.ChatService.send_message", return_value="Hi!"):
            resp = client.post(
                "/v1/chat?agent_id=general",
                json={"query": "Follow up question", "session_id": session_id},
            )

        assert resp.status_code == 200

    def test_chat_unknown_agent_returns_404(self, client: TestClient):
        """A non-existent agent_id that can't be auto-seeded should 404."""
        resp = client.post(
            "/v1/chat?agent_id=nonexistent_agent_xyz",
            json={"query": "Hello"},
        )
        assert resp.status_code == 404

    def test_chat_missing_body_returns_422(self, client: TestClient):
        """POST /chat without a body should fail validation."""
        resp = client.post("/v1/chat")
        assert resp.status_code == 422

    # ── GET /chat/sessions ─────────────────────────────────────────────────────

    def test_list_sessions_returns_list(self, client: TestClient):
        """GET /chat/sessions should always return a sessions list."""
        resp = client.get("/v1/chat/sessions")
        assert resp.status_code == 200
        body = resp.json()
        assert "sessions" in body
        assert isinstance(body["sessions"], list)

    # ── POST /chat/sessions ────────────────────────────────────────────────────

    def test_create_session(self, client: TestClient):
        """POST /chat/sessions should create a new session and return its id."""
        resp = client.post("/v1/chat/sessions?title=My+Test+Chat")
        assert resp.status_code == 200
        body = resp.json()
        assert "session_id" in body
        assert "title" in body
        assert body["title"] == "My Test Chat"

    # ── GET /chat/sessions/{id} ────────────────────────────────────────────────

    def test_get_session_messages(self, client: TestClient):
        """GET /chat/sessions/{id} should return a messages list."""
        db = TestingSessionLocal()
        conv = ChatConversation(user_id=_DEV_USER_ID, title="Direct Session")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id
        db.close()

        resp = client.get(f"/v1/chat/sessions/{conv_id}")
        assert resp.status_code == 200
        assert "messages" in resp.json()
        assert isinstance(resp.json()["messages"], list)

    # ── DELETE /chat/sessions/{id} ─────────────────────────────────────────────

    def test_delete_session(self, client: TestClient):
        """DELETE /chat/sessions/{id} should delete the session."""
        db = TestingSessionLocal()
        conv = ChatConversation(user_id=_DEV_USER_ID, title="To Delete")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        session_id = conv.id
        db.close()

        resp = client.delete(f"/v1/chat/sessions/{session_id}")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

        db = TestingSessionLocal()
        assert db.query(ChatConversation).filter_by(id=session_id).first() is None
        db.close()

    def test_delete_nonexistent_session_returns_404(self, client: TestClient):
        """DELETE on a session that doesn't exist should return 404."""
        resp = client.delete("/v1/chat/sessions/does-not-exist-at-all")
        assert resp.status_code == 404

    # ── DELETE /chat/sessions/{id}/messages/{msg_id} ──────────────────────────

    def test_delete_message(self, client: TestClient):
        """DELETE /chat/sessions/{id}/messages/{msg_id} removes a message."""
        db = TestingSessionLocal()
        conv = ChatConversation(user_id=_DEV_USER_ID, title="Session With Msg")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = ChatMessage(conversation_id=conv.id, role="user", content="hi")
        db.add(msg)
        db.commit()
        db.refresh(msg)
        conv_id, msg_id = conv.id, msg.id
        db.close()

        resp = client.delete(f"/v1/chat/sessions/{conv_id}/messages/{msg_id}")
        assert resp.status_code == 200

        db = TestingSessionLocal()
        assert db.query(ChatMessage).filter_by(id=msg_id).first() is None
        db.close()
