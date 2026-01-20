import time
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from .context import AgentContext
from .prompts import HUMAN_MESSAGE_TEMPLATE, REPORT_GENERATION_SYSTEM_PROMPT
from .state import AgentState


def embed_query(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if runtime.context.embedding is None:
        raise ValueError("Missing embedding model")
    if runtime.context.tokenizer is None:
        raise ValueError("Missing tokenizer model")
    if state.input_query is None:
        raise ValueError("Input query cannot be empty")
    res = runtime.context.embedding.embed_query(
        text=state.input_query,
        tokenizer=runtime.context.tokenizer,
        event_name="retrieval agent",
    )
    embedding = res.embedding
    res = res.model_dump()
    res.pop("embedding")
    return state.model_copy(update={"embedded_query": embedding, "run_metadata": res})


def search(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if runtime.context.db_client is None:
        raise ValueError("Missing vector database client")
    if runtime.context.collection_name is None:
        raise ValueError("Collection name cannot be none")
    if state.embedded_query is None or not isinstance(state.embedded_query, list):
        raise ValueError(
            f"Embedding query cannot be of type {type(state.embedded_query)}"
        )
    if isinstance(state.embedded_query[0], float):
        state.embedded_query = [state.embedded_query]
    start_time = time.time()
    res = runtime.context.db_client.search(
        collection_name=runtime.context.collection_name,
        anns_field="vector",
        data=state.embedded_query,
        output_fields=["text", "category", "source"],
        limit=3,
        # TODO: connect this later in agent context
        search_params={
            "radius": 0.5,  # Lower score threshold
            "range_filter": 1.0,  # Upper score threshold
        },
    )
    search_duration_ms = (time.time() - start_time) * 1000
    res = res[0]
    res = [{**doc.fields, "score": doc.score * 100, "id": doc.id} for doc in res]
    sources = [doc["source"] for doc in res]
    return state.model_copy(
        update={
            "documents": res,
            "sources": sources,
            "run_metadata": {
                "search_duration_ms": search_duration_ms,
                **state.run_metadata,
            },
        }
    )


def final_report_generation(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    if runtime.context.chat_model is None:
        raise ValueError("Missing vector database client")
    messages: list[BaseMessage] = [
        SystemMessage(content=REPORT_GENERATION_SYSTEM_PROMPT),
        HumanMessage(
            content=HUMAN_MESSAGE_TEMPLATE.format(
                user_query=state.input_query, relevant_documents=str(state.documents)
            )
        ),
    ]
    result = runtime.context.chat_model.invoke(messages)
    result = result.content
    return state.model_copy(update={"final_answer": result})


def should_use_llm(
    _: AgentState, runtime: Runtime[AgentContext]
) -> Literal["__end__", "final_report_generation"]:
    if runtime.context.include_generation:
        return "final_report_generation"
    return "__end__"
