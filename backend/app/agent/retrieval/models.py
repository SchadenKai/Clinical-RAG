import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RelevantDocs(BaseModel):
    text: str
    vector: Optional[list[float]]
    source: str = Field(description="Will contain the source link for the document")

    # this is to support metadata
    model_config = ConfigDict(extra="allow")


class ProgressStatusEnum(enum.Enum):
    LOADING_FILE = "Loading File"
    CHUNKING = "Chunking"
    BUILDING_DOCS = "Building Final Document"
    INDEXING = "Indexing"
    DONE = "Done"
