from langchain_core.documents import Document
from langgraph.runtime import Runtime

from app.agent.indexing.context import AgentContext
from app.agent.indexing.state import AgentState
from app.logger import app_logger
from .models import ProgressStatusEnum


def document_loader(state: AgentState) -> AgentState:
    """
    1. Loads the file from S3 Storage using the file path from state.filepath
    2. Parse the file to retrieve text / even convert to markdown
    3. Update the state.raw_document
    """
    fake_docs = Document(
        page_content="This is just a testing", metadata={"source": "http://testing.com"}
    )
    return AgentState(
        raw_document=[fake_docs],
        progress_status=ProgressStatusEnum.LOADING_FILE,
    )


def chunker_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    chunker = runtime.context.chunker

    # TODO: Change this into custom excetion to comply with sonarqube
    if chunker is None:
        print("[ERROR] Chunker / Text splitter cannot be left empty")
        return state
    if state.raw_document is None:
        print("[ERROR] Raw string parsed from the file cannot be empty")
        return state

    docs = chunker.split_documents(state.raw_document)

    return AgentState(
        chunked_documents=docs, progress_status=ProgressStatusEnum.CHUNKING
    )


def doc_builder_node(state: AgentState, runtime: Runtime[AgentContext]) -> AgentState:
    encoder = runtime.context.encoder
    tokenizer = runtime.context.tokenizer
    if encoder is None:
        print("[ERROR] Encoder / Embedding model cannot be left empty")
        return state
    if state.chunked_documents is None:
        print("[ERROR] Chunked documents from the chunker cannot be empty")
        return state
    if tokenizer is None:
        print("[ERROR] Tokenizer cannot be empty")
        return state

    text_list = [doc.page_content for doc in state.chunked_documents]
    embed_results = encoder.embed_documents(text_list, tokenizer)
    vector_list = embed_results.embeding
    app_logger.info(
        f"Token count: {embed_results.token_count} Total cost: {embed_results.total_cost} Duration ms: {embed_results.duration_ms}"
    )
    final_doc_list = []
    for i, doc in enumerate(state.chunked_documents):
        final_doc = {
            "text": doc.page_content,
            "source": doc.metadata["source"],
            "vector": vector_list[i],
            **doc.metadata,
        }
        final_doc_list.append(final_doc)

    return AgentState(
        final_documents=final_doc_list, progress_status=ProgressStatusEnum.BUILDING_DOCS
    )


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
    return AgentState(progress_status=ProgressStatusEnum.DONE)
