"""
API integration tests for /settings endpoints.
LLM and Embedding config CRUD.
"""

from fastapi.testclient import TestClient

from app.db.models import EmbeddingConfig, LLMConfig


class TestSettingsEndpoints:
    """Tests for GET/PUT /settings/llm and /settings/embedding."""

    # ── GET /settings/llm ─────────────────────────────────────────────────────

    def test_get_llm_settings_returns_config(self, client: TestClient):
        """Should return the active LLM config (seeded in conftest)."""
        resp = client.get("/v1/settings/llm")
        assert resp.status_code == 200
        body = resp.json()
        assert "provider" in body
        assert "model_name" in body
        assert body["api_key"] == "***"  # Never expose API keys

    # ── PUT /settings/llm ─────────────────────────────────────────────────────

    def test_update_llm_settings(self, client: TestClient, db):
        """PUT should create a new active LLM config."""
        resp = client.put(
            "/v1/settings/llm",
            json={
                "provider": "nebius",
                "model_name": "Qwen/Qwen3-14B-instruct",
                "api_key": "sk-nebius-key",
            },
        )
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

        # Confirm only one active record now
        active_count = db.query(LLMConfig).filter(LLMConfig.is_active).count()
        assert active_count == 1

        # Previous should be deactivated
        latest = db.query(LLMConfig).filter(LLMConfig.is_active).first()
        assert latest.provider == "nebius"
        assert latest.model_name == "Qwen/Qwen3-14B-instruct"

    # ── GET /settings/embedding ────────────────────────────────────────────────

    def test_get_embedding_settings_returns_config(self, client: TestClient):
        """Should return the active embedding config (seeded in conftest)."""
        resp = client.get("/v1/settings/embedding")
        assert resp.status_code == 200
        body = resp.json()
        assert "provider" in body
        assert "model_name" in body
        assert body["api_key"] == "***"

    # ── PUT /settings/embedding ────────────────────────────────────────────────

    def test_update_embedding_settings_marks_docs_pending(
        self, client: TestClient, db
    ):
        """PUT /settings/embedding should return 202 + documents_affected count."""
        from app.db.models import Document

        # Seed some documents
        for i in range(3):
            doc = Document(
                source="who",
                filename=f"doc_{i}.pdf",
                status="INDEXED",
            )
            db.add(doc)
        db.commit()

        resp = client.put(
            "/v1/settings/embedding",
            json={
                "provider": "openai",
                "model_name": "text-embedding-3-large",
                "api_key": "sk-new-key",
            },
        )
        assert resp.status_code == 202
        body = resp.json()
        assert "documents_affected" in body
        assert body["documents_affected"] >= 3  # At least our seeded docs
        assert "warning" in body["message"].lower()

        # Verify all docs are now PENDING
        pending = db.query(Document).filter(Document.status == "PENDING").count()
        assert pending >= 3

    def test_update_embedding_settings_deactivates_previous(
        self, client: TestClient, db
    ):
        """Only one embedding config should be active after updating."""
        client.put(
            "/v1/settings/embedding",
            json={
                "provider": "huggingface",
                "model_name": "BAAI/bge-m3",
                "api_key": "hf-key",
            },
        )
        active_count = (
            db.query(EmbeddingConfig).filter(EmbeddingConfig.is_active).count()
        )
        assert active_count == 1
