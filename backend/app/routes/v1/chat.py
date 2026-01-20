from typing import Annotated, cast

from fastapi import APIRouter, Depends
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

# from ag_ui.core import RunAgentInput
# from ag_ui.encoder import EventEncoder
from app.agent.react_agent.context import AgentContext
from app.agent.react_agent.main import agent
from app.agent.react_agent.state import AgentState
from app.services.llm.factory import get_chat_model_service
from app.utils import get_request_id

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("")
def send_message(
    query: str,
    request_id: Annotated[str, Depends(get_request_id)],
    llm: Annotated[BaseChatModel, Depends(get_chat_model_service)],
    system_prompt: str | None = "You are a helpful assistant",
):
    init_state = AgentState(
        messages=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]
    )
    context = AgentContext(llm=llm)
    config: RunnableConfig = {"configurable": {"thread_id": request_id}}
    final_response = ""
    for res in agent.stream(input=init_state, context=context, config=config):
        for _, state_update in res.items():
            if "messages" in state_update:
                final_message = cast(BaseMessage, state_update["messages"][-1])
                final_response = final_message.content

    return final_response


# @chat_router.post("/ag-ui/stream")
# def send_message_agui(req: Request):
#     # used for encoding response
#     encoder = EventEncoder()
