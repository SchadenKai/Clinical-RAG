from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Document


class IndexingStatusService:
    def __init__(self, db: Session):
        self.db = db

    def get_overall_status(self) -> dict[str, dict[str, Any]]:
        """
        Returns group counts by source and status.
        E.g. {"who": {"INDEXED": 10, "PENDING": 2}, "cdc": {"INDEXED": 5}}
        """
        results = (
            self.db.query(Document.source, Document.status, func.count(Document.id))
            .group_by(Document.source, Document.status)
            .all()
        )

        summary = {}
        for source, status, count in results:
            if source not in summary:
                summary[source] = {}
            summary[source][status] = count

        return summary

    def get_documents_by_source(self, source: str) -> list[Document]:
        """Get all documents for a specific source."""
        return (
            self.db.query(Document)
            .filter(Document.source == source)
            .order_by(Document.created_at.desc())
            .all()
        )

    def get_document_status(self, document_id: str) -> Document:
        """Get a specific document's status."""
        return self.db.query(Document).filter(Document.id == document_id).first()
