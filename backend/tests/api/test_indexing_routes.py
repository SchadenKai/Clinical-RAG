"""
API integration tests for /indexing endpoints.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.models import Document


class TestIndexingEndpoints:
    """Tests for POST /indexing/trigger/*, POST /indexing/upload, GET /indexing/status."""

    # ── POST /indexing/trigger/who ─────────────────────────────────────────────

    def test_trigger_who_indexing(self, client: TestClient):
        """POST /indexing/trigger/who should return a 200 and a message."""
        with patch("app.routes.v1.indexing.get_indexing_service") as mock_svc:
            mock_svc.return_value = MagicMock()
            resp = client.post("/v1/indexing/trigger/who")

        assert resp.status_code == 200
        assert "who" in resp.json()["message"].lower()

    # ── POST /indexing/trigger/cdc ─────────────────────────────────────────────

    def test_trigger_cdc_indexing(self, client: TestClient):
        """POST /indexing/trigger/cdc should return a 200 and a message."""
        with patch("app.routes.v1.indexing.get_indexing_service") as mock_svc:
            mock_svc.return_value = MagicMock()
            resp = client.post("/v1/indexing/trigger/cdc")

        assert resp.status_code == 200
        assert "cdc" in resp.json()["message"].lower()

    # ── POST /indexing/upload ──────────────────────────────────────────────────

    def test_upload_file(self, client: TestClient):
        """POST /indexing/upload should accept a file and return success."""
        mock_indexing_svc = MagicMock()
        mock_indexing_svc.upload_file.return_value = None
        mock_indexing_svc.ingest_document.return_value = {}

        with patch(
            "app.routes.v1.indexing.get_indexing_service",
            return_value=mock_indexing_svc,
        ):
            resp = client.post(
                "/v1/indexing/upload",
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "filename" in body
        assert body["filename"] == "test.pdf"

    # ── GET /indexing/status ───────────────────────────────────────────────────

    def test_get_overall_status_empty(self, client: TestClient):
        """GET /indexing/status should return a dict (possibly empty)."""
        resp = client.get("/v1/indexing/status")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_get_overall_status_with_documents(self, client: TestClient, db):
        """GET /indexing/status should show counts grouped by source + status."""
        db.add(Document(source="who", filename="a.pdf", status="INDEXED"))
        db.add(Document(source="who", filename="b.pdf", status="PENDING"))
        db.add(Document(source="cdc", filename="c.pdf", status="INDEXED"))
        db.commit()

        resp = client.get("/v1/indexing/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "who" in body
        assert "INDEXED" in body["who"]
        assert "cdc" in body

    # ── GET /indexing/status/{item_id} ────────────────────────────────────────

    def test_get_item_status_found(self, client: TestClient, db):
        """GET /indexing/status/{id} should return details of a known document."""
        doc = Document(source="cdc", filename="specific.pdf", status="INDEXING")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.get(f"/v1/indexing/status/{doc.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == doc.id
        assert body["status"] == "INDEXING"
        assert body["filename"] == "specific.pdf"

    def test_get_item_status_not_found(self, client: TestClient):
        """GET /indexing/status/{id} for unknown id returns error."""
        resp = client.get("/v1/indexing/status/nonexistent-doc-id-xyz")
        assert resp.status_code == 200  # Returns {"error": "Document not found"}
        assert "error" in resp.json()
