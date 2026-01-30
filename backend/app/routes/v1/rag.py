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


@rag_router.post("/extract")
def extract_md_content_from_file(
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    file_key: str,
):
    return indexing_service.extract_md_content(file_key)


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

@rag_router.post("/evaluate")
def evaluate_rag_system(
    evaluation_pipeline: Annotated[
        EvaluationPipeline, Depends(get_evaluation_pipeline)
    ],
):
    faithfulness_test_cases = [
        # TEST CASE 1: The "Invented Cure" (Hallucination)
        # Scenario: The context mentions prevention, but the model invents a cure.
        LLMTestCase(
            input="What is the recommended treatment for the new 'Zeta' variant?",
            # The model answers confidently with a specific drug not in the context.
            actual_output="The CDC recommends immediate administration of Hydroxy-Zeta-Mectin for all patients.",
            retrieval_context=[
                "The 'Zeta' variant is currently under investigation. No specific antiviral treatments have yet been approved for this specific variant. Supportive care is recommended."
            ],
            expected_output="There are no specific antiviral treatments approved yet; supportive care is recommended.",
        ),
        # TEST CASE 2: The "Contradiction"
        # Scenario: The model gives advice directly opposite to the WHO guidelines in the context.
        LLMTestCase(
            input="Is the malaria vaccine recommended for travelers to Country X?",
            actual_output="No, the malaria vaccine is generally not needed for travelers to Country X.",
            retrieval_context=[
                "WHO designates Country X as a high-risk zone. The RTS,S/AS01 malaria vaccine is strongly recommended for all travelers entering the region."
            ],
            expected_output="Yes, the WHO strongly recommends the vaccine for travelers to Country X.",
        ),
    ]
    return evaluation_pipeline.evaluate(faithfulness_test_cases)


@rag_router.post("/generate/golden")
def generate_golden_dataset(
    synthetic_data_generator: Annotated[
        SyntheticDataGenerator, Depends(get_synthetic_data_generator)
    ],
):
    return synthetic_data_generator.generate()
