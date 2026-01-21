import re
import time
from typing import Literal

import validators
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from .context import AgentContext
from .models import SafetyClassificationEnum, SafetyClassifierSOModel
from .prompts import (
    FIX_CITATION_PROMPT,
    HUMAN_MESSAGE_TEMPLATE,
    REFUSAL_AGENT_HUMAN_PROMPT_TEMPLATE,
    REFUSAL_AGENT_SYSTEM_PROMPT,
    REPORT_GENERATION_SYSTEM_PROMPT,
    SAFETY_CLASSIFIER_HUMAN_MESSAGE_TEMPLATE,
    SAFETY_CLASSIFIER_SYSTEM_PROMPT,
)
from .state import AgentState

_SAFETY_CLASSIFICATION_THRESHOLD = 0.3


def safety_classifier_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    """
    Classifies the user's query in terms of the SafetyClassfication
    """
    if state.input_query is None:
        raise ValueError("Missing user input query")
    if runtime.context.chat_model is None:
        raise ValueError("Missing vector database client")

    messages: list[BaseMessage] = [
        SystemMessage(content=SAFETY_CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(
            content=SAFETY_CLASSIFIER_HUMAN_MESSAGE_TEMPLATE.format(
                user_query=state.input_query
            )
        ),
    ]
    chat_model = runtime.context.chat_model.with_structured_output(
        schema=SafetyClassifierSOModel
    )
    response: SafetyClassifierSOModel = chat_model.invoke(messages)
    return state.model_copy(update={"safety_classification": response})


def is_query_safe(state: AgentState) -> Literal["embed_query", "refusal_node"]:
    if (
        state.safety_classification.classification == SafetyClassificationEnum.SAFE
        or state.safety_classification.confidence_score
        < _SAFETY_CLASSIFICATION_THRESHOLD
    ):
        return "embed_query"
    return "refusal_node"


def refusal_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if state.input_query is None:
        raise ValueError("Missing user input query")
    if state.safety_classification.supporting_args is None:
        raise ValueError("Supporting arguments cannot be empty")
    if runtime.context.chat_model is None:
        raise ValueError("Missing vector database client")

    messages: list[BaseMessage] = [
        SystemMessage(content=REFUSAL_AGENT_SYSTEM_PROMPT),
        HumanMessage(
            content=REFUSAL_AGENT_HUMAN_PROMPT_TEMPLATE.format(
                user_query=state.input_query,
                classification=state.safety_classification.classification,
                supporting_args=state.safety_classification.supporting_args,
            )
        ),
    ]
    res = runtime.context.chat_model.invoke(messages)
    return state.model_copy(update={"final_answer": res.content})


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
    system_prompt = (
        REPORT_GENERATION_SYSTEM_PROMPT
        if state.is_verified_citations
        else REPORT_GENERATION_SYSTEM_PROMPT
        + FIX_CITATION_PROMPT.format(wrong_citations=state.wrong_citations)
    )
    messages: list[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=HUMAN_MESSAGE_TEMPLATE.format(
                user_query=state.input_query,
                relevant_documents=str(state.documents),
            )
        ),
    ]
    result = runtime.context.chat_model.invoke(messages)
    result = result.content
    return state.model_copy(update={"final_answer": result})


def citation_verification(state: AgentState) -> AgentState:
    if state.final_answer is None:
        raise ValueError("The final answer cannot be empty")
    if state.sources is None:
        raise ValueError("Source list cannot be empty")

    citation_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    citation_list: list[str, str] = re.findall(citation_pattern, state.final_answer)
    # TODO: change this into a pydantic model instead
    wrong_citations = []
    is_verified_citation = True
    for citation in citation_list:
        if not citation[0].strip().isdigit():
            wrong_citations.append(citation)
            is_verified_citation = False
            continue
        if not validators.url(citation[1]):
            wrong_citations.append(citation)
            is_verified_citation = False
            continue
        if state.sources[int(citation[0])] != citation[1]:
            wrong_citations.append(citation)
            is_verified_citation = False

    if is_verified_citation:
        return state
    return state.model_copy(
        update={
            "is_verified_citations": is_verified_citation,
            "wrong_citations": wrong_citations,
        }
    )


def is_citation_correct(
    state: AgentState,
) -> Literal["final_report_generation", "__end__"]:
    if state.is_verified_citations:
        return "__end__"
    return "final_report_generation"


def should_use_llm(
    _: AgentState, runtime: Runtime[AgentContext]
) -> Literal["__end__", "final_report_generation"]:
    if runtime.context.include_generation:
        return "final_report_generation"
    return "__end__"
