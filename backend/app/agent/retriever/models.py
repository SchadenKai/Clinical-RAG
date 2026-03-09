import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class SafetyClassificationEnum(enum.Enum):
    SAFE = "Safe"
    UNSAFE_MEDICAL = "Unsafe medical"
    UNSAFE_HARMFUL = "Unsafe harmful"
    OFF_TOPIC = "off topic"


class SafetyClassifierSOModel(BaseModel):
    classification: SafetyClassificationEnum = Field(
        "classification of the user's query based on the available classes"
    )
    supporting_args: list[str] = Field(
        description="List of arguments that supports the classification claim"
    )
    confidence_score: float = Field(
        description=(
            "Indicate the confidence score for the given classification."
            "Be skeptical when it comes to classifying user queries ensuring"
            "priority towards precision classification rather than recall."
        ),
        ge=0.0,
        le=1.0,
    )


class QueryGeneratorSOModel(BaseModel):
    queries: list[str] = Field(
        description=(
            "List of search queries generated from the user's input. "
            "For simple queries, return a single query. For complex queries, "
            "return multiple distinct queries covering different aspects. "
            "Must contain at least 1 query."
        ),
    )

    @field_validator("queries")
    @classmethod
    def queries_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("queries must contain at least 1 query")
        return v
