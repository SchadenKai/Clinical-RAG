from typing import Annotated

from fastapi import APIRouter, Depends
from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig

from app.agent.indexing.context import AgentContext
from app.agent.indexing.main import agent
from app.agent.indexing.state import AgentState
from app.core.config import settings
from app.rag.chunker import get_chunker
from app.rag.db import VectorClient, get_vector_client
from app.rag.embeddings import EmbeddingService, get_bi_encoder, get_embedding
from app.services.llm.tokenizer import TokenizerService, get_tokenizer
from app.utils import get_request_id

rag_router = APIRouter(prefix="/rag", tags=["rag"])


@rag_router.post("/ingest")
def ingest_document(
    encoder: Annotated[Embeddings, Depends(get_bi_encoder)],
    vector_db: Annotated[VectorClient, Depends(get_vector_client)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    chunker = get_chunker("recursive")
    collection_name = settings.milvus_collection_name
    db_client = vector_db.client

    init_state = AgentState(file_path="test")
    context = AgentContext(
        chunker=chunker,
        encoder=encoder,
        db_client=db_client,
        collection_name=collection_name,
    )
    config: RunnableConfig = {"configurable": {"thread_id": request_id}}

    for res in agent.stream(input=init_state, context=context, config=config):
        for status_updates in res.items():
            if "progress_status" in status_updates:
                print(status_updates["progress_status"])
    return None


@rag_router.post("/test/embed")
def test_embed_query(
    query: str,
    embed: Annotated[EmbeddingService, Depends(get_embedding)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer)],
) -> list[float]:
    return embed.embed_query(query, tokenizer)


@rag_router.post("/test/embed/batch")
def test_embed_queries(
    query_list: list[str],
    embed: Annotated[EmbeddingService, Depends(get_embedding)],
    tokenizer: Annotated[TokenizerService, Depends(get_tokenizer)],
) -> list[list[float]]:
    return embed.embed_documents(query_list, tokenizer)
