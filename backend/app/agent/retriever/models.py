import enum
from typing import Literal, Optional

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
        min_length=1,
        description=(
            "List of search queries generated from the user's input. "
            "For simple queries, return a single query. For complex queries, "
            "return multiple distinct queries covering different aspects. "
            "Must contain at least 1 query."
        ),
    )


class LLMJudgeState(BaseModel):
    """Composite state container for all LLM-as-a-Judge related fields."""

    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall quality score from 0.0 to 1.0 (minimum of context and answer scores)",
    )
    address_back: Optional[Literal["query_generation", "synthesizer"]] = Field(
        default=None,
        description=(
            "Routing target when quality is insufficient: "
            "'query_generation' if retrieved context is lacking, "
            "'synthesizer' if synthesis quality is poor"
        ),
    )
    feedback: Optional[str] = Field(
        default=None,
        description="GEval reason explaining the score and guiding the next iteration",
    )
    iterations: int = Field(
        default=0,
        description="Number of judge evaluation iterations completed",
    )
    all_documents: Optional[list[dict]] = Field(
        default=None,
        description="Accumulated retrieved documents across all judge iterations (deduplicated)",
    )
