from typing import Optional

from docling_core.transforms.chunker.doc_chunk import DocChunk
from docling_core.types.doc.document import DoclingDocument
from pydantic import BaseModel, ConfigDict

from app.agent.indexing.models import ProgressStatusEnum, RelevantDocs


class AgentState(BaseModel):
    website_url: Optional[str] = None
    file_key: Optional[str] = None
    raw_document: Optional[DoclingDocument] = None
    chunked_documents: Optional[list[DocChunk]] = None
    final_documents: Optional[list[RelevantDocs]] = None
    progress_status: Optional[ProgressStatusEnum] = None
    run_metadata: Optional[dict] = None
    pipeline_metadata: Optional[dict] = None
    chunk_metadata_list: Optional[list[dict]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
