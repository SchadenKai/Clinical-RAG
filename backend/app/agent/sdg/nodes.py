import datetime
import json
from pathlib import PurePosixPath

from langchain_core.documents import Document
from langgraph.runtime import Runtime
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.testset.graph import KnowledgeGraph, Node, NodeType
from ragas.testset.transforms import apply_transforms, default_transforms

from app.logger import app_logger
from app.services.document_converter import doc_converter
from app.services.file_store.context_manager import S3FileStager

from .context import AgentContext
from .models import SdgProgressEnum
from .state import AgentState


def file_ingestion_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict:
    app_logger.info("SDG: ingesting file %s", state.file_key)
    with S3FileStager(
        runtime.context.s3_service,
        state.file_key,
        runtime.context.settings,
    ) as file_path:
        content = doc_converter(
            file_path,
            page_batch_size=runtime.context.settings.pdf_batch_size,
        )
    return {
        "raw_document": content,
        "progress_status": SdgProgressEnum.LOADING_FILE,
    }


def document_preparation_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> dict:
    markdown = state.raw_document.export_to_markdown()
    langchain_doc = Document(
        page_content=markdown,
        metadata={"source": state.file_key},
    )
    app_logger.info(
        "SDG: prepared LangChain Document (%d chars) from %s",
        len(markdown),
        state.file_key,
    )
    return {
        "langchain_documents": [langchain_doc],
        "progress_status": SdgProgressEnum.PREPARING_DOCUMENTS,
    }


def knowledge_graph_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict:
    app_logger.info(
        "SDG: building knowledge graph from %d document(s)",
        len(state.langchain_documents),
    )
    ragas_llm = LangchainLLMWrapper(runtime.context.llm_service.client)
    ragas_embeddings = LangchainEmbeddingsWrapper(
        runtime.context.embedding_service.client
    )

    nodes = [
        Node(
            type=NodeType.DOCUMENT,
            properties={
                "page_content": doc.page_content,
                "document_metadata": doc.metadata,
            },
        )
        for doc in state.langchain_documents
    ]
    kg = KnowledgeGraph(nodes=nodes)

    transforms = default_transforms(
        documents=state.langchain_documents,
        llm=ragas_llm,
        embedding_model=ragas_embeddings,
    )

    try:
        # apply_transforms calls apply_nest_asyncio internally; safe from sync node
        apply_transforms(kg, transforms)
    except ValueError as e:
        app_logger.warning(
            "SDG: apply_transforms raised ValueError (document may be too short): %s", e
        )

    app_logger.info(
        "SDG: KG built — %d nodes, %d relationships",
        len(kg.nodes),
        len(kg.relationships),
    )
    return {
        "knowledge_graph": kg,
        "progress_status": SdgProgressEnum.BUILDING_KNOWLEDGE_GRAPH,
    }


def testset_generation_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict:
    from ragas.testset import TestsetGenerator

    app_logger.info("SDG: generating testset of size %d", state.testset_size)
    ragas_llm = LangchainLLMWrapper(runtime.context.llm_service.client)
    ragas_embeddings = LangchainEmbeddingsWrapper(
        runtime.context.embedding_service.client
    )

    generator = TestsetGenerator(
        llm=ragas_llm,
        embedding_model=ragas_embeddings,
        knowledge_graph=state.knowledge_graph,
    )

    try:
        testset = generator.generate(testset_size=state.testset_size)
        goldens = testset.to_list()
    except Exception as e:
        app_logger.error("SDG: testset generation failed: %s", e)
        goldens = []

    app_logger.info("SDG: generated %d golden samples", len(goldens))
    return {
        "goldens": goldens,
        "progress_status": SdgProgressEnum.GENERATING_TESTSET,
    }


def store_goldens_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict:
    if not state.goldens:
        app_logger.warning("SDG: no goldens to store")
        return {"progress_status": SdgProgressEnum.DONE}

    settings = runtime.context.settings
    s3_client = runtime.context.s3_service.client

    file_stem = PurePosixPath(state.file_key).stem
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_key = f"goldens/{file_stem}_{timestamp}.json"

    payload = json.dumps(state.goldens, ensure_ascii=False, indent=2).encode("utf-8")
    s3_client.put_object(
        Bucket=settings.minio_bucket_name,
        Key=output_key,
        Body=payload,
        ContentType="application/json",
    )

    app_logger.info("SDG: stored %d goldens at %s", len(state.goldens), output_key)
    return {
        "output_path": output_key,
        "progress_status": SdgProgressEnum.DONE,
    }
