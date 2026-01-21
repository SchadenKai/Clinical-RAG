from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import SafetyClassifierSOModel


class AgentState(BaseModel):
    input_query: str
    embedded_query: Optional[list[float] | list[list[float]]] = None
    final_answer: Optional[str] = None
    documents: Optional[list[dict]] = None
    sources: Optional[list[str]] = None
    run_metadata: Optional[dict] = None
    safety_classification: Optional[SafetyClassifierSOModel] = None
    is_verified_citations: bool = True
    wrong_citations: Optional[list] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
