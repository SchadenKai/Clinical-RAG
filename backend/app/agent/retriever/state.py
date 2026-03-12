from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import LLMJudgeState, SafetyClassifierSOModel


class AgentState(BaseModel):
    input_query: str
    generated_queries: Optional[list[str]] = None
    embedded_query: Optional[list[list[float]]] = None
    final_answer: Optional[str] = None
    documents: Optional[list[dict]] = None
    sources: Optional[list[str]] = None
    run_metadata: Optional[dict] = None
    safety_classification: Optional[SafetyClassifierSOModel] = None
    is_verified_citations: bool = True
    wrong_citations: Optional[list] = None
    llm_judge_state: Optional[LLMJudgeState] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
