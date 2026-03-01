from typing import Annotated

from fastapi import APIRouter, Depends
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.core.config import Settings
from app.rag.db import VectorClient
from app.routes.dependencies.auth import get_current_user
from app.routes.dependencies.chat_agent import get_chat_agent
from app.routes.dependencies.llm import get_chat_model_service
from app.routes.dependencies.rag import get_retrieval_service
from app.routes.dependencies.settings import get_app_settings
from app.routes.dependencies.vector_db import get_vector_client
from app.services.llm.factory import ChatModelService
from app.services.rag import RetrievalService
from app.utils import get_request_id

vector_db_router = APIRouter(prefix="/vector_db", tags=["vector_db"])


class SearchRequest(BaseModel):
    query: str


@vector_db_router.post("/search")
def search_vector_db(
    payload: SearchRequest,
    request_id: Annotated[str, Depends(get_request_id)],
    chat_agent: Annotated[CompiledStateGraph, Depends(get_chat_agent)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    current_user: Annotated[object, Depends(get_current_user)],
):
    """
    Search endpoint that uses the adaptive LLM flow with the 'clinical_rag' agent.
    This replaces a direct retrieval call.
    """
    from langchain_core.messages import HumanMessage

    from app.agent.chat.context import AgentContext
    from app.agent.chat.tools import clinical_retrieval_tool

    runtime_tools = [clinical_retrieval_tool]

    context = AgentContext(
        llm=chat_model_service.client,
        tools=runtime_tools,
        retrieval_service=retrieval_service,
        settings=settings,
    )

    init_state = {"messages": [HumanMessage(content=payload.query)]}

    final_response = ""
    stream_config = {"configurable": {"thread_id": request_id}}

    for res in chat_agent.stream(
        input=init_state, config=stream_config, context=context
    ):
        for _node_name, state_update in res.items():
            if "messages" in state_update and state_update["messages"]:
                final_message = state_update["messages"][-1]
                if hasattr(final_message, "content"):
                    final_response = final_message.content

    return {"result": final_response}


@vector_db_router.delete("/collection")
def clear_collection(
    vector_service: Annotated[VectorClient, Depends(get_vector_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    vector_client = vector_service.client
    try:
        vector_client.use_database(settings.milvus_db_name)
        vector_client.drop_collection(settings.milvus_collection_name)
        vector_service.setup()
        vector_service.load_collection()
    except Exception as e:
        raise RuntimeError(f"Something went wrong during deletion: {e}") from e
    return None
