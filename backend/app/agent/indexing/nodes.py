import asyncio
import json

from crawl4ai import CrawlResult
from langchain_core.documents import Document
from langgraph.runtime import Runtime

from app.services.scrapper import structured_output_scrapper

from .context import AgentContext
from .models import ProgressStatusEnum
from .state import AgentState


def web_scrapper(state: AgentState) -> AgentState:
    results: CrawlResult = asyncio.run(structured_output_scrapper(state.website_url))
    results = json.loads(results.extracted_content)
    results: dict = results[0]
    print(results)
    doc = Document(
        page_content=results["page_content"],
        metadata={
            "source": state.website_url,
            "page_title": results["title"],
            "published_date": results["date"],
        },
    )
    if results.get("tags"):
        doc.metadata["tags"] = [tag["name"] for tag in results["tags"]]

    return {
        "raw_document": [doc],
        "progress_status": ProgressStatusEnum.LOADING_FILE,
    }


def chunker_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    chunker = runtime.context.chunker

    if chunker is None:
        print("[ERROR] Chunker / Text splitter cannot be left empty")
        return state
    if state.raw_document is None:
        print("[ERROR] Raw string parsed from the file cannot be empty")
        return state

    docs = chunker.split_documents(state.raw_document)

    return {"chunked_documents": docs, "progress_status": ProgressStatusEnum.CHUNKING}


def doc_builder_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    embedding = runtime.context.embedding
    tokenizer = runtime.context.tokenizer
    if embedding is None:
        print("[ERROR] embedding / Embedding model cannot be left empty")
        return state
    if state.chunked_documents is None:
        print("[ERROR] Chunked documents from the chunker cannot be empty")
        return state
    if tokenizer is None:
        print("[ERROR] Tokenizer cannot be empty")
        return state

    text_list = [doc.page_content for doc in state.chunked_documents]
    res = embedding.embed_documents(
        text_list, tokenizer, event_name="indexing batch documents"
    )
    vector_list = res.embedding
    res = res.model_dump()
    res.pop("embedding")

    final_doc_list = []
    for i, doc in enumerate(state.chunked_documents):
        final_doc = {
            "text": doc.page_content,
            "source": doc.metadata["source"],
            "vector": vector_list[i],
            **doc.metadata,
        }
        final_doc_list.append(final_doc)

    return {
        "final_documents": final_doc_list,
        "progress_status": ProgressStatusEnum.BUILDING_DOCS,
        "run_metadata": {**res},
    }


def indexing_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    db_client = runtime.context.db_client
    collection_name = runtime.context.collection_name

    if db_client is None:
        print("[ERROR] Vector database client cannot be left empty")
        return state
    if collection_name is None:
        print("[ERROR] Collection name cannot be left empty")
        return state
    if state.final_documents is None:
        print("[ERROR] Final documents from the final document builder cannot be empty")
        return state

    data = [doc.model_dump() for doc in state.final_documents]
    db_client.insert(collection_name=collection_name, data=data)
    return state.model_copy(update={"progress_status": ProgressStatusEnum.DONE})
