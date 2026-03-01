from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Document
from app.services.file_store.db import S3Service


class CatalogService:
    def __init__(self, db: Session, s3_service: S3Service, settings: Settings):
        self.db = db
        self.s3_service = s3_service
        self.settings = settings

    def get_catalog(
        self,
        source: Optional[str] = None,
        search_query: Optional[str] = None,
        status: Optional[str] = "INDEXED",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        """Returns paginated catalog items."""
        query = self.db.query(Document)

        if status and status.upper() != "ALL":
            query = query.filter(Document.status == status.upper())

        if source:
            query = query.filter(Document.source == source)

        if search_query:
            query = query.filter(Document.filename.ilike(f"%{search_query}%"))

        return (
            query.order_by(Document.indexed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_document_details(self, document_id: str) -> Optional[dict]:
        """Get metadata and a presigned URL to view the file."""
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return None

        presigned_url = None
        try:
            s3_client = self.s3_service.client
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.settings.minio_bucket_name,
                    # Document.url stores the bucket object key
                    "Key": doc.url,
                },
                ExpiresIn=3600,
            )
        except Exception as e:
            from app.logger import app_logger

            app_logger.error(f"Failed to generate presigned URL for {document_id}: {e}")

        return {"document": doc, "presigned_url": presigned_url}
