from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.routes.dependencies.auth import get_current_user
from app.routes.dependencies.db_session import get_db
from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.settings import get_app_settings
from app.services.catalog_service import CatalogService
from app.services.file_store.db import S3Service

catalog_router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_service(
    db: Annotated[Session, Depends(get_db)],
    s3_service: Annotated[S3Service, Depends(get_s3_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> CatalogService:
    return CatalogService(db=db, s3_service=s3_service, settings=settings)


@catalog_router.get("")
def get_catalog(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[object, Depends(get_current_user)],
    source: Optional[str] = Query(None, description="Filter by source"),
    q: Optional[str] = Query(None, description="Search term for filename"),
    status: Optional[str] = Query(
        "INDEXED", description="Filter by status or 'ALL' for no filter"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get documents, optionally filtered by source, status or search query."""
    docs = catalog_service.get_catalog(
        source=source, search_query=q, status=status, limit=limit, offset=offset
    )
    return {"items": [d.__dict__ for d in docs]}


@catalog_router.get("/{doc_id}")
def get_document(
    doc_id: str,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    """Get document details and a presigned URL to view it."""
    result = catalog_service.get_document_details(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_dict = result["document"].__dict__.copy()
    if "_sa_instance_state" in doc_dict:
        del doc_dict["_sa_instance_state"]

    return {"document": doc_dict, "view_url": result["presigned_url"]}
