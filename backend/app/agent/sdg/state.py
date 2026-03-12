from typing import Any, Optional

from docling_core.types.doc.document import DoclingDocument
from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field

from app.agent.sdg.models import SdgProgressEnum


class AgentState(BaseModel):
    # Input fields
    file_key: str
    testset_size: int = Field(default=10, ge=1, le=100)

    # Pipeline intermediate state
    raw_document: Optional[DoclingDocument] = None
    langchain_documents: Optional[list[Document]] = None
    # KnowledgeGraph is a @dataclass; stored as Any to avoid Pydantic validation.
    # InMemorySaver holds by reference (no JSON roundtrip), so this is safe.
    knowledge_graph: Optional[Any] = None
    goldens: Optional[list[dict]] = None

    # Output
    output_path: Optional[str] = None
    progress_status: Optional[SdgProgressEnum] = None
    error: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
