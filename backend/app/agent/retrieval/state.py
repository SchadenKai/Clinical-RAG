from typing import Optional

from pydantic import BaseModel, ConfigDict


class AgentState(BaseModel):
    input_query: str
    embedded_query: Optional[list[float] | list[list[float]]] = None
    final_llm_report: Optional[str] = None
    documents: Optional[list[dict]] = None
    sources: Optional[list[str]] = None
    run_metadata: Optional[dict] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
