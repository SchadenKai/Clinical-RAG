from typing import Annotated, cast

from fastapi import APIRouter, Depends
from langchain_core.runnables import RunnableConfig

# INDEXING AGENT deps
from app.agent.indexing.context import AgentContext as IndexingAgentContext
from app.agent.indexing.main import agent as indexing_agent
from app.agent.indexing.state import AgentState as IndexingAgentState
from app.agent.retrieval.context import AgentContext as InferenceAgentContext
from app.agent.retrieval.main import agent as inference_agent
from app.agent.retrieval.state import AgentState as InferenceAgentState
from app.core.config import settings
from app.rag.chunker import get_chunker
from app.rag.db import VectorClient, get_vector_client
from app.rag.embeddings import EmbeddingService, get_embedding
from app.rag.models import EmbeddingResponseModel
from app.services.llm.factory import ChatModelService, get_chat_model_service
from app.services.llm.tokenizer import TokenizerService, get_tokenizer_service
from app.utils import get_request_id

rag_router = APIRouter(prefix="/rag", tags=["rag"])


@rag_router.post("/ingest")
def ingest_document(
    website_url: str,
    encoder: Annotated[EmbeddingService, Depends(get_embedding)],
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    chunker = get_chunker("recursive")
    collection_name = settings.milvus_collection_name
    db_client = vector_db.client

    init_state = IndexingAgentState(website_url=website_url)
    context = IndexingAgentContext(
        chunker=chunker,
        embedding=encoder,
        tokenizer=tokenizer,
        db_client=db_client,
        collection_name=collection_name,
    )
    config: RunnableConfig = {"configurable": {"thread_id": request_id}}
    final_response = {}
    for res in indexing_agent.stream(input=init_state, context=context, config=config):
        for node_name, state in res.items():
            if "indexing_node" in node_name:
                final_response = state["run_metadata"]
    return final_response


@rag_router.post("/retrieve")
def retrieve_documents(
    query: str,
    encoder: Annotated[EmbeddingService, Depends(get_embedding)],
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    chat_model_service: Annotated[ChatModelService, Depends(get_chat_model_service)],
    run_llm: bool = False,
):
    chunker = get_chunker("recursive")
    collection_name = settings.milvus_collection_name
    db_client = vector_db.client
    chat_model = chat_model_service.client

    init_state = InferenceAgentState(input_query=query)
    context = InferenceAgentContext(
        chunker=chunker,
        embedding=encoder,
        tokenizer=tokenizer,
        db_client=db_client,
        chat_model=chat_model,
        collection_name=collection_name,
        include_generation=run_llm,
    )
    config: RunnableConfig = {"configurable": {"thread_id": request_id}}
    final_response = {}
    for res in inference_agent.stream(input=init_state, context=context, config=config):
        for _, state in res.items():
            if state:
                state = cast(dict, state)
                state.pop("embedded_query")
                final_response = state
    return final_response


@rag_router.post("/test/embed")
def test_embed_query(
    query: str,
    embed: Annotated[EmbeddingService, Depends(get_embedding)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
) -> EmbeddingResponseModel:
    return embed.embed_query(query, tokenizer)


@rag_router.post("/test/embed/batch")
def test_embed_queries(
    query_list: list[str],
    embed: Annotated[EmbeddingService, Depends(get_embedding)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer_service)],
) -> EmbeddingResponseModel:
    return embed.embed_documents(query_list, tokenizer)
