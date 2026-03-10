import asyncio
import datetime
import json
from zoneinfo import ZoneInfo

from docling_core.transforms.chunker.doc_chunk import DocChunk
from docling_core.types.doc.document import DoclingDocument, DocumentOrigin
from docling_core.types.doc.labels import DocItemLabel
from langgraph.runtime import Runtime

from app.logger import app_logger
from app.services.document_converter import doc_converter
from app.services.file_store.context_manager import S3FileStager
from app.services.scrapper import structured_output_scrapper

from .context import AgentContext
from .models import ProgressStatusEnum, SourceClass
from .state import AgentState
from .utils import clean_chunk_content, hash_text


def web_scrapper(state: AgentState) -> AgentState:
    results = asyncio.run(structured_output_scrapper(state.website_url))
    results = json.loads(results.extracted_content)
    results: dict = results[0]

    page_content = results.get("page_content", "")
    title = results.get("title", "web_document")

    dl_doc = DoclingDocument(
        name=title,
        origin=DocumentOrigin(
            mimetype="text/html",
            filename="web_scraped.html",
            binary_hash=int(hash_text(page_content)[:16], 16),
            uri=state.website_url,
        ),
    )
    dl_doc.add_heading(text=title, level=1)
    if page_content:
        dl_doc.add_text(label=DocItemLabel.PARAGRAPH, text=page_content)

    pipeline_metadata = {
        "source": state.website_url,
        "page_title": title,
        "source_type": "web",
        "published_date": results.get("date"),
    }
    if results.get("tags"):
        pipeline_metadata["tags"] = [tag["name"] for tag in results["tags"]]

    return {
        "raw_document": dl_doc,
        "pipeline_metadata": pipeline_metadata,
        "progress_status": ProgressStatusEnum.LOADING_FILE,
    }


def file_ingestion_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    with S3FileStager(
        runtime.context.s3_service, state.file_key, runtime.context.settings
    ) as file_path:
        content = doc_converter(file_path)

    pipeline_metadata = {
        "source": state.file_key,
        "page_title": content.name,
        "source_type": "file",
    }

    return {
        "raw_document": content,
        "pipeline_metadata": pipeline_metadata,
        "progress_status": ProgressStatusEnum.LOADING_FILE,
    }


def chunker_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    chunker = runtime.context.chunker

    if chunker is None:
        app_logger.error("Chunker cannot be left empty")
        return state
    if state.raw_document is None:
        app_logger.error("Raw document cannot be empty")
        return state

    chunks = list(chunker.chunk(state.raw_document))

    return {"chunked_documents": chunks, "progress_status": ProgressStatusEnum.CHUNKING}


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


def _derive_source(chunk: DocChunk, pipeline_metadata: dict) -> str:
    origin = chunk.meta.origin if chunk.meta else None
    if origin:
        if origin.uri:
            return str(origin.uri)
        if origin.filename:
            return origin.filename
    return pipeline_metadata.get("source", "")


def metadata_builder_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> AgentState:
    if state.chunked_documents is None:
        app_logger.error("Chunked documents cannot be empty")
        return state
    if runtime.context.settings is None:
        app_logger.error("Settings cannot be empty")
        return state

    timezone = ZoneInfo(runtime.context.settings.timezone)
    pipeline_meta = state.pipeline_metadata or {}
    final_chunks = []
    final_metadata = []

    for i, chunk in enumerate(state.chunked_documents):
        cleaned_text = clean_chunk_content(chunk.text)

        content_hash = hash_text(cleaned_text)

        runtime.context.db_client.use_database(runtime.context.settings.milvus_db_name)
        # content_hash is SHA-256 hex — only [0-9a-f] chars, safe for f-string interpolation
        duplicate = runtime.context.db_client.query(
            filter=f"content_hash == '{content_hash}'",
            collection_name=runtime.context.settings.milvus_collection_name,
            output_fields=["id"],
        )
        if duplicate:
            app_logger.warning(
                "Duplicate found. Removing duplicate chunk no. %d from the list of chunks", i
            )
            continue

        source = _derive_source(chunk, pipeline_meta)

        chunk_metadata = {
            **pipeline_meta,
            "source": source,
            "content_hash": content_hash,
            "chunk_index": len(final_chunks),
            "prev_chunk_id": len(final_chunks) - 1 if len(final_chunks) > 0 else 0,
            "next_chunk_id": (
                i + 1
                if i < len(state.chunked_documents) - 1
                else len(state.chunked_documents)
            ),
            "last_updated": datetime.datetime.now(tz=timezone).isoformat(),
            "source_class": _source_metadata(website_url=state.website_url).value,
            "headings": (chunk.meta.headings if chunk.meta else []) or [],
        }

        final_chunks.append(chunk)
        final_metadata.append(chunk_metadata)

    return state.model_copy(
        update={
            "chunked_documents": final_chunks,
            "chunk_metadata_list": final_metadata,
        }
    )


def doc_builder_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    embedding = runtime.context.embedding
    tokenizer = runtime.context.tokenizer
    if embedding is None:
        app_logger.error("Embedding model cannot be left empty")
        return state
    if state.chunked_documents is None:
        app_logger.error("Chunked documents from the chunker cannot be empty")
        return state
    if tokenizer is None:
        app_logger.error("Tokenizer cannot be empty")
        return state

    text_list = [clean_chunk_content(chunk.text) for chunk in state.chunked_documents]
    res = embedding.embed_documents(
        text_list, tokenizer, event_name="indexing batch documents"
    )
    vector_list = res.embedding
    res = res.model_dump()
    res.pop("embedding")

    chunk_metadata_list = state.chunk_metadata_list or [
        {} for _ in state.chunked_documents
    ]

    final_doc_list = []
    for i, (chunk, cleaned_text) in enumerate(zip(state.chunked_documents, text_list)):
        meta = chunk_metadata_list[i] if i < len(chunk_metadata_list) else {}
        final_doc = {
            "text": cleaned_text,
            "source": meta.get("source", ""),
            "vector": vector_list[i],
            **meta,
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
        app_logger.error("Vector database client cannot be left empty")
        return state
    if collection_name is None:
        app_logger.error("Collection name cannot be left empty")
        return state
    if state.final_documents is None:
        app_logger.error("Final documents from the final document builder cannot be empty")
        return state

    data = list(state.final_documents)
    db_client.insert(collection_name=collection_name, data=data)
    return state.model_copy(update={"progress_status": ProgressStatusEnum.DONE})
