"""
API integration tests for /catalog endpoints.
"""

from fastapi.testclient import TestClient

from app.db.models import Document


class TestCatalogEndpoints:
    """Tests for GET /catalog and GET /catalog/{doc_id}."""

    def _seed_documents(self, db):
        """Helper: insert a set of documents and return them."""
        docs = [
            Document(source="who", filename="who_guide.pdf", status="INDEXED", url="who/who_guide.pdf"),
            Document(source="who", filename="who_report.pdf", status="INDEXED", url="who/who_report.pdf"),
            Document(source="cdc", filename="cdc_brief.pdf", status="INDEXED", url="cdc/cdc_brief.pdf"),
            Document(source="upload", filename="local_doc.pdf", status="PENDING", url=None),
        ]
        for d in docs:
            db.add(d)
        db.commit()
        for d in docs:
            db.refresh(d)
        return docs

    # ── GET /catalog ───────────────────────────────────────────────────────────

    def test_get_catalog_returns_items(self, client: TestClient, db):
        """GET /catalog should return a list of INDEXED documents."""
        self._seed_documents(db)

        resp = client.get("/v1/catalog")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        # Only INDEXED documents should appear
        statuses = {item.get("status") for item in body["items"]}
        assert "PENDING" not in statuses

    def test_get_catalog_filter_by_source(self, client: TestClient, db):
        """GET /catalog?source=who should only return WHO documents."""
        resp = client.get("/v1/catalog?source=who")
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["source"] == "who"

    def test_get_catalog_filter_by_search(self, client: TestClient, db):
        """GET /catalog?q=brief should only return docs with 'brief' in filename."""
        resp = client.get("/v1/catalog?q=brief")
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert "brief" in item["filename"].lower()

    def test_get_catalog_pagination(self, client: TestClient, db):
        """GET /catalog?limit=1&offset=0 should only return 1 item."""
        resp = client.get("/v1/catalog?limit=1&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 1

    # ── GET /catalog/{doc_id} ──────────────────────────────────────────────────

    def test_get_document_detail_found(self, client: TestClient, db):
        """GET /catalog/{id} for a known doc returns metadata + presigned url."""
        from unittest.mock import MagicMock, patch

        doc = Document(source="who", filename="detail_doc.pdf", status="INDEXED", url="who/detail_doc.pdf")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        with patch("app.services.catalog_service.S3Service") as MockS3:
            mock_s3 = MagicMock()
            mock_s3.client.generate_presigned_url.return_value = "https://presigned.url/detail_doc.pdf"
            MockS3.return_value = mock_s3

            resp = client.get(f"/v1/catalog/{doc.id}")

        assert resp.status_code == 200
        body = resp.json()
        assert "document" in body
        assert body["document"]["id"] == doc.id

    def test_get_document_detail_not_found(self, client: TestClient):
        """GET /catalog/{id} for non-existent doc returns 404."""
        resp = client.get("/v1/catalog/totally-nonexistent-doc-id-abc")
        assert resp.status_code == 404
