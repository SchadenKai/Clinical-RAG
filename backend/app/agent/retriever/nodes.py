import logging
import re
import time
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from pymilvus import AnnSearchRequest, RRFRanker

from app.logger import app_logger

from .context import AgentContext
from .models import (
    LLMJudgeState,
    QueryGeneratorSOModel,
    SafetyClassificationEnum,
    SafetyClassifierSOModel,
)
from .prompts import (
    FIX_CITATION_PROMPT,
    HUMAN_MESSAGE_TEMPLATE,
    JUDGE_ANSWER_QUALITY_CRITERIA,
    JUDGE_CONTEXT_SUFFICIENCY_CRITERIA,
    JUDGE_FEEDBACK_PROMPT,
    QUERY_GENERATOR_HUMAN_MESSAGE_TEMPLATE,
    QUERY_GENERATOR_HUMAN_MESSAGE_TEMPLATE_WITH_FEEDBACK,
    QUERY_GENERATOR_SYSTEM_PROMPT,
    REFUSAL_AGENT_HUMAN_PROMPT_TEMPLATE,
    REFUSAL_AGENT_SYSTEM_PROMPT,
    REPORT_GENERATION_SYSTEM_PROMPT,
    SAFETY_CLASSIFIER_HUMAN_MESSAGE_TEMPLATE,
    SAFETY_CLASSIFIER_SYSTEM_PROMPT,
)
from .state import AgentState

_SAFETY_CLASSIFICATION_THRESHOLD = 0.3
logger = logging.getLogger(__name__)


def safety_classifier_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    """
    Classifies the user's query in terms of the SafetyClassfication
    """
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


def is_query_safe(state: AgentState) -> Literal["generate_queries", "refusal_node"]:
    if (
        state.safety_classification.classification == SafetyClassificationEnum.SAFE
        or state.safety_classification.confidence_score
        < _SAFETY_CLASSIFICATION_THRESHOLD
    ):
        return "generate_queries"
    return "refusal_node"


def refusal_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
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


def generate_queries(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if runtime.context.chat_model is None:
        raise ValueError("Missing chat model")

    has_judge_feedback = state.llm_judge_state and state.llm_judge_state.feedback
    if has_judge_feedback:
        human_content = QUERY_GENERATOR_HUMAN_MESSAGE_TEMPLATE_WITH_FEEDBACK.format(
            user_query=state.input_query,
            judge_feedback=state.llm_judge_state.feedback,
        )
    else:
        human_content = QUERY_GENERATOR_HUMAN_MESSAGE_TEMPLATE.format(
            user_query=state.input_query
        )

    messages: list[BaseMessage] = [
        SystemMessage(content=QUERY_GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]
    chat_model = runtime.context.chat_model.with_structured_output(
        schema=QueryGeneratorSOModel
    )
    try:
        response: QueryGeneratorSOModel = chat_model.invoke(messages)
        return state.model_copy(update={"generated_queries": response.queries})
    except Exception as e:
        logger.warning("Query generation failed, falling back to original query: %s", e)
        return state.model_copy(update={"generated_queries": [state.input_query]})


def embed_query(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if runtime.context.embedding is None:
        raise ValueError("Missing embedding model")
    if runtime.context.tokenizer is None:
        raise ValueError("Missing tokenizer model")
    if state.input_query is None:
        raise ValueError("Input query cannot be empty")

    queries = state.generated_queries or [state.input_query]
    embeddings = []
    total_token_count = 0
    total_cost = 0.0
    total_duration_ms = 0.0

    for query in queries:
        res = runtime.context.embedding.embed_query(
            text=query,
            tokenizer=runtime.context.tokenizer,
            event_name="retrieval agent",
        )
        embeddings.append(res.embedding)
        total_token_count += res.token_count
        total_cost += res.total_cost
        total_duration_ms += res.duration_ms

    run_meta = {
        "token_count": total_token_count,
        "total_cost": total_cost,
        "duration_ms": total_duration_ms,
    }
    return state.model_copy(
        update={"embedded_query": embeddings, "run_metadata": run_meta}
    )


def search(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if runtime.context.db_client is None:
        raise ValueError("Missing vector database client")
    if runtime.context.settings.milvus_collection_name is None:
        raise ValueError("Collection name cannot be none")
    if state.embedded_query is None or not isinstance(state.embedded_query, list):
        raise ValueError(
            f"Embedding query cannot be of type {type(state.embedded_query)}"
        )
    start_time = time.time()
    runtime.context.db_client.use_database(runtime.context.settings.milvus_db_name)

    text_queries = state.generated_queries or [state.input_query]
    search_limit = runtime.context.settings.search_limit
    dense_req = AnnSearchRequest(
        data=state.embedded_query,
        anns_field="vector",
        param={"metric_type": "IP", "params": {"radius": 0.5, "range_filter": 1.0}},
        limit=search_limit,
    )
    sparse_req = AnnSearchRequest(
        data=text_queries,
        anns_field="sparse_vector",
        param={"metric_type": "BM25"},
        limit=search_limit,
    )

    res = runtime.context.db_client.hybrid_search(
        collection_name=runtime.context.settings.milvus_collection_name,
        reqs=[dense_req, sparse_req],
        ranker=RRFRanker(k=runtime.context.settings.rrf_k),
        output_fields=[
            "text",
            "source",
            "source_class",
            "page_title",
            "chunk_index",
            "headings",
        ],
        limit=runtime.context.settings.reranker_top_k * 3,
        search_params={
            "radius": 0.5,  # Lower score threshold
            "range_filter": 1.0,  # Upper score threshold
        },
    )
    search_duration_ms = (time.time() - start_time) * 1000
    all_docs = []
    for group in res:
        all_docs.extend(
            [{**doc.entity, "score": doc.distance, "id": doc.id} for doc in group]
        )
    seen_ids: dict = {}
    for doc in all_docs:
        doc_id = doc.get("id")
        if doc_id not in seen_ids or (
            doc.get("score", 0) > seen_ids[doc_id].get("score", 0)
        ):
            seen_ids[doc_id] = doc
    res = [
        doc
        for doc in seen_ids.values()
        if doc.get("score", 0) >= runtime.context.settings.search_score_threshold
    ]

    # Consolidate new docs with accumulated docs from previous judge iterations
    accumulated = {
        doc["id"]: doc
        for doc in (
            (state.llm_judge_state.all_documents if state.llm_judge_state else None)
            or []
        )
    }
    for doc in res:
        doc_id = doc.get("id")
        if doc_id not in accumulated or doc.get("score", 0) > accumulated[doc_id].get(
            "score", 0
        ):
            accumulated[doc_id] = doc
    merged = list(accumulated.values())

    sources = [doc.get("source") for doc in merged]

    current_judge = state.llm_judge_state or LLMJudgeState()
    updated_judge = current_judge.model_copy(update={"all_documents": merged})

    return state.model_copy(
        update={
            "documents": merged,
            "sources": sources,
            "llm_judge_state": updated_judge,
            "run_metadata": {
                "search_duration_ms": search_duration_ms,
                **state.run_metadata,
            },
        }
    )


def rerank_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    if not state.documents:
        return state

    start_time = time.time()
    reranked_docs = runtime.context.reranker.rerank(
        query=state.input_query,
        documents=state.documents,
        top_k=runtime.context.settings.reranker_top_k,
    )
    rerank_duration_ms = (time.time() - start_time) * 1000

    sources = [doc.get("source") for doc in reranked_docs if "source" in doc]

    # Update run metadata if needed
    new_metadata = dict(state.run_metadata) if state.run_metadata else {}
    new_metadata["rerank_duration_ms"] = rerank_duration_ms

    return state.model_copy(
        update={
            "documents": reranked_docs,
            "sources": sources,
            "run_metadata": new_metadata,
        }
    )


def final_report_generation(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    if runtime.context.chat_model is None:
        raise ValueError("Missing vector database client")
    system_prompt = REPORT_GENERATION_SYSTEM_PROMPT
    if not state.is_verified_citations:
        system_prompt += FIX_CITATION_PROMPT.format(
            wrong_citations=state.wrong_citations
        )
    elif (
        state.llm_judge_state
        and state.llm_judge_state.feedback
        and state.llm_judge_state.iterations > 0
    ):
        system_prompt += JUDGE_FEEDBACK_PROMPT.format(
            judge_feedback=state.llm_judge_state.feedback,
            previous_answer=state.final_answer or "",
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
    wrong_citations = []
    is_verified_citation = True

    if "【" in state.final_answer or "】" in state.final_answer:
        wrong_citations.append("FORMAT_ERROR: Found invalid brackets 【 】")
        is_verified_citation = False

    citation_pattern = r"\[(\d+)\]\(([^)]+)\)"
    citation_list: list[str, str] = re.findall(citation_pattern, state.final_answer)

    for citation in citation_list:
        if not citation[0].strip().isdigit():
            wrong_citations.append(
                f"TYPE ERROR: Citation index in {citation} is not a digit "
            )
            is_verified_citation = False
            continue
        if int(citation[0]) >= len(state.sources) or int(citation[0]) < 0:
            wrong_citations.append(
                f"INDEX ERROR: Citation index in {citation} is not the correct."
                f"Citations: {state.sources}"
                f"Documents: {state.documents}"
            )
            is_verified_citation = False
            continue
        if state.sources[int(citation[0])] != citation[1]:
            wrong_citations.append(
                f"INDEX ERROR: Reference link is not correct in {citation}"
                f"Citations: {state.sources}"
                f"Documents: {state.documents}"
            )
            is_verified_citation = False

    if is_verified_citation:
        return state.model_copy(
            update={
                "is_verified_citations": is_verified_citation,
                "wrong_citations": [],
            }
        )
    return state.model_copy(
        update={
            "is_verified_citations": is_verified_citation,
            "wrong_citations": wrong_citations,
        }
    )


def is_citation_correct(
    state: AgentState,
) -> Literal["final_report_generation", "llm_judge_node"]:
    app_logger.debug(f"Checking citation state: {state.is_verified_citations}")
    if state.is_verified_citations:
        return "llm_judge_node"
    app_logger.debug(f"Wrong citations: {state.wrong_citations}")
    return "final_report_generation"


def should_use_llm(
    _: AgentState, runtime: Runtime[AgentContext]
) -> Literal["__end__", "final_report_generation"]:
    if runtime.context.include_generation:
        return "final_report_generation"
    return "__end__"


def llm_judge_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    """
    Evaluates the final answer quality using two DeepEval GEval metrics:
    1. RAG Context Sufficiency — are the retrieved docs enough to answer the query?
    2. RAG Answer Quality — does the synthesis faithfully use the docs?

    Routing logic (set in llm_judge.address_back):
    - 'query_generation': context is lacking → retrieve additional documents
    - 'synthesizer': context is sufficient but synthesis is poor → refine the answer
    """
    from deepeval.metrics import GEval
    from deepeval.models import GPTModel
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    settings = runtime.context.settings
    judge_model = GPTModel(
        model=settings.llm_model_name,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    test_case = LLMTestCase(
        input=state.input_query,
        actual_output=state.final_answer or "",
        retrieval_context=[doc.get("text", "") for doc in (state.documents or [])],
    )

    context_metric = GEval(
        name="RAG Context Sufficiency",
        criteria=JUDGE_CONTEXT_SUFFICIENCY_CRITERIA,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        model=judge_model,
        threshold=settings.judge_score_threshold,
        async_mode=False,
    )
    quality_metric = GEval(
        name="RAG Answer Quality",
        criteria=JUDGE_ANSWER_QUALITY_CRITERIA,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        model=judge_model,
        threshold=settings.judge_score_threshold,
        async_mode=False,
    )

    try:
        context_metric.measure(test_case)
        quality_metric.measure(test_case)

        ctx_score = context_metric.score or 0.0
        qual_score = quality_metric.score or 0.0
        overall_score = min(ctx_score, qual_score)

        # Context deficiency takes routing priority over synthesis deficiency
        if ctx_score < settings.judge_score_threshold:
            address_back = "query_generation"
            feedback = context_metric.reason or ""
        elif qual_score < settings.judge_score_threshold:
            address_back = "synthesizer"
            feedback = quality_metric.reason or ""
        else:
            address_back = None
            feedback = ""
    except Exception as exc:
        logger.error("LLM judge evaluation failed: %s", exc)
        overall_score = 0.0
        address_back = "query_generation"
        feedback = f"Judge evaluation failed: {exc}"

    current_judge = state.llm_judge_state or LLMJudgeState()
    updated_judge = current_judge.model_copy(
        update={
            "score": overall_score,
            "address_back": address_back,
            "feedback": feedback,
            "iterations": current_judge.iterations + 1,
        }
    )
    return state.model_copy(update={"llm_judge_state": updated_judge})


def judge_decision(
    state: AgentState, runtime: Runtime[AgentContext]
) -> Literal["__end__", "final_report_generation", "generate_queries"]:
    """
    Routes after llm_judge_node:
    - __end__: score passes threshold or max iterations reached
    - final_report_generation: synthesis needs refinement
    - generate_queries: additional document retrieval needed
    """
    threshold = runtime.context.settings.judge_score_threshold
    max_iter = runtime.context.settings.judge_max_iterations
    judge = state.llm_judge_state

    if (
        judge is None
        or (judge.score is not None and judge.score >= threshold)
        or judge.iterations >= max_iter
    ):
        return "__end__"
    if judge.address_back == "synthesizer":
        return "final_report_generation"
    return "generate_queries"
