import asyncio
from typing import Annotated, Optional

from deepeval.test_case import LLMTestCase
from fastapi import APIRouter, Depends, UploadFile

# INDEXING AGENT deps
from app.routes.dependencies.data_generator import get_synthetic_data_generator
from app.routes.dependencies.evaluator import get_evaluation_pipeline
from app.routes.dependencies.rag import get_indexing_service, get_retrieval_service
from app.services.evaluation.dataset import SyntheticDataGenerator
from app.services.evaluation.evaluator import EvaluationPipeline
from app.services.rag import IndexingService, RetrievalService
from pydantic import BaseModel
from app.services.scrapper import who_pdf_list_scrapper
from app.utils import get_request_id

rag_router = APIRouter(prefix="/rag", tags=["rag"])


@rag_router.post("/ingest")
def ingest_website(
    website_url: str,
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    return indexing_service.ingest_website(
        website_url=website_url, request_id=request_id
    )


@rag_router.post("/ingest/file")
def ingest_document(
    file_key: str,
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    return indexing_service.ingest_document(file_key=file_key, request_id=request_id)


@rag_router.post("/upload")
def upload_file_route(
    file: Optional[UploadFile],
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
):
    return indexing_service.upload_file(pdf_file=file.file, filename=file.filename)


@rag_router.get("/objects/all")
def get_object_list(
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    file_name: Optional[str] = None,
) -> list[str]:
    return indexing_service.get_object_list(file_name)


@rag_router.post("/retrieve")
def retrieve_documents(
    query: str,
    retriever_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    is_llm_enabled: bool = False,
):
    return retriever_service.retrieve_documents(
        query=query,
        is_llm_enabled=is_llm_enabled,
        request_id=request_id,
    )


#### API FOR TESTING ONLY ####
# TODO: remove this later after integrating this into the evaluation pipeline


class EvaluationRequestBody(BaseModel):
    user_input: str
    actual_output: str
    retrieved_context: list[str]
    expected_output: str
    expected_contexts: list[str]


@rag_router.post("/test/evaluate")
def evaluate_rag_system(
    request: EvaluationRequestBody,
    evaluation_pipeline: Annotated[
        EvaluationPipeline, Depends(get_evaluation_pipeline)
    ],
):
    test_case = LLMTestCase(
        input=request.user_input,
        actual_output=request.actual_output,
        context=request.expected_contexts,
        retrieval_context=request.retrieved_context,
        expected_output=request.expected_output,
    )
    return evaluation_pipeline.evaluate([test_case])


@rag_router.post("/test/generate/golden")
def generate_golden_dataset(
    synthetic_data_generator: Annotated[
        SyntheticDataGenerator, Depends(get_synthetic_data_generator)
    ],
):
    return synthetic_data_generator.generate()


@rag_router.post("/test/scrape")
def simple_scrapping_test(
    website_url: str,
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
) -> str:
    return indexing_service.test_scrapping_and_extraction(website_url=website_url)


@rag_router.post("/test/extract")
def document_extrctor_test(
    file: Optional[UploadFile],
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    file_url: str | None = None,
) -> str:
    return indexing_service.test_doc_extraction(file.file, file.filename, file_url)


@rag_router.post("/test/who_pdf_list_scrapper")
def pdf_scrapper_test(website_url: str) -> str:
    response = asyncio.run(who_pdf_list_scrapper(website_url))
    return response
