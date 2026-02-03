import asyncio
import datetime
import json
import threading
from zoneinfo import ZoneInfo

from crawl4ai import CrawlResult
from langchain_core.documents import Document
from langgraph.runtime import Runtime

from app.services.file_store.context_manager import S3FileStager
from app.services.scrapper import document_extractor, structured_output_scrapper

from .context import AgentContext
from .models import ProgressStatusEnum, SourceClass
from .state import AgentState
from .utils import clean_chunk_content, hash_text


def _store_report_locally(docs: list[Document], file_path: str):
    flattened_docs = [doc.model_dump() for doc in docs]
    with open(file=file_path, mode="w") as file:
        json.dump(flattened_docs, file, indent=4)


def web_scrapper(state: AgentState) -> AgentState:
    results: CrawlResult = asyncio.run(structured_output_scrapper(state.website_url))
    results = json.loads(results.extracted_content)
    results: dict = results[0]
    doc = Document(
        page_content=results["page_content"],
        metadata={
            "source": state.website_url,
            "page_title": results["title"],
            "published_date": results["date"],
            "source_type": "web",
        },
    )
    if results.get("tags"):
        doc.metadata["tags"] = [tag["name"] for tag in results["tags"]]

    threading.Thread(
        target=_store_report_locally,
        args=(
            doc,
            "app/data/reports/scraped_data.json",
        ),
    ).run()
    return {
        "raw_document": [doc],
        "progress_status": ProgressStatusEnum.LOADING_FILE,
    }


def file_ingestion_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    with S3FileStager(
        runtime.context.s3_service, state.file_key, runtime.context.settings
    ) as file_path:
        content = document_extractor(file_path)

    doc = Document(
        page_content=content.export_to_markdown(),
        metadata={
            "source": state.file_key,
            "page_title": content.name,
            "source_type": "file",
        },
    )
    threading.Thread(
        target=_store_report_locally,
        args=(
            doc,
            "app/data/reports/scraped_data.json",
        ),
    ).run()
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


def _source_metadata(website_url: str) -> SourceClass:
    # category metadata
    if website_url:
        if SourceClass.WHO.value.lower() in website_url:
            source_class = SourceClass.WHO
        elif SourceClass.CDC.value.lower() in website_url:
            source_class = SourceClass.CDC
        else:
            source_class = SourceClass.OTHERS
    else:
        source_class = SourceClass.OTHERS
    return source_class


def metadata_builder_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    if state.chunked_documents is None:
        print("[ERROR] Chunked documents cannot be empty")
        return state
    if runtime.context.settings is None:
        print("[ERROR] Settings cannot be empty")
        return state

    timezone = ZoneInfo(runtime.context.settings.timezone)
    final_doc_list = []
    for i, doc in enumerate(state.chunked_documents):
        cleaned_text = clean_chunk_content(doc.page_content)
        doc.page_content = cleaned_text

        content_hash = hash_text(cleaned_text)
        runtime.context.db_client.use_database(runtime.context.settings.milvus_db_name)
        duplicate = runtime.context.db_client.query(
            filter=f"content_hash  == '{doc.metadata['content_hash']}'",
            collection_name=runtime.context.settings.milvus_collection_name,
            output_fields=["id"],
        )
        if duplicate:
            print(
                "[WARNING] Duplicate found. Removing duplicate "
                f"chunk no. {i} from the list of chunks"
            )
            continue
        doc.metadata["content_hash"] = content_hash

        doc.metadata["chunk_index"] = i
        doc.metadata["prev_chunk_id"] = i - 1 if i > 0 else 0
        doc.metadata["next_chunk_id"] = (
            i + 1 if i < len(state.chunked_documents) else len(state.chunked_documents)
        )

        doc.metadata["last_updated"] = datetime.datetime.now(tz=timezone).isoformat()
        doc.metadata["source_class"] = _source_metadata(
            website_url=state.website_url
        ).value

        final_doc_list.append(doc)
    threading.Thread(
        target=_store_report_locally,
        args=(
            final_doc_list,
            "app/data/reports/chunked_data.json",
        ),
    ).run()
    return state.model_copy(update={"chunked_documents": final_doc_list})


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
    collection_name = runtime.context.settings.milvus_collection_name

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
