from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from app.routes.dependencies.auth import get_current_user
from app.routes.dependencies.db_session import get_db
from app.routes.dependencies.rag import get_indexing_service
from app.services.indexing_status import IndexingStatusService
from app.services.rag import IndexingService

indexing_router = APIRouter(prefix="/indexing", tags=["indexing"])


def get_indexing_status_service(
    db: Annotated[object, Depends(get_db)],
) -> IndexingStatusService:
    return IndexingStatusService(db=db)


@indexing_router.post("/trigger/who")
def trigger_who_indexing(
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    # This should be offloaded to a background task
    return {"message": "WHO indexing triggered"}


@indexing_router.post("/trigger/cdc")
def trigger_cdc_indexing(
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    return {"message": "CDC indexing triggered"}


@indexing_router.post("/upload")
def upload_file(
    file: UploadFile,
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    import uuid

    indexing_service.upload_file(pdf_file=file.file, filename=file.filename)
    request_id = str(uuid.uuid4())
    indexing_service.ingest_document(file_key=file.filename, request_id=request_id)
    return {"message": "File uploaded and indexing started", "filename": file.filename}


@indexing_router.get("/status")
def get_overall_status(
    status_service: Annotated[
        IndexingStatusService, Depends(get_indexing_status_service)
    ],
    current_user: Annotated[object, Depends(get_current_user)],
):
    """Returns indexing status grouped by source"""
    return status_service.get_overall_status()


@indexing_router.get("/status/{item_id}")
def get_item_status(
    item_id: str,
    status_service: Annotated[
        IndexingStatusService, Depends(get_indexing_status_service)
    ],
    current_user: Annotated[object, Depends(get_current_user)],
):
    """Returns status of a specific document"""
    doc = status_service.get_document_status(item_id)
    if not doc:
        return {"error": "Document not found"}
    return {
        "id": doc.id,
        "source": doc.source,
        "status": doc.status,
        "filename": doc.filename,
    }
