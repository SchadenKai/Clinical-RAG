"""
Run this script by running:
cd backend && uv run python -m app.scripts.create_retrieval_report
"""

import json
from concurrent.futures import ThreadPoolExecutor

from app.routes.dependencies.rag import get_retriever_service_manual
from app.services.rag import RetrievalService
from app.utils import get_request_id

retrieval_service: RetrievalService = get_retriever_service_manual()

with open("app/data/reports/synthetic_golden_dataset.json") as file:
    dataset = json.load(file)

queries = [data["input"] for data in dataset]
request_ids = [get_request_id() for _ in queries]
is_llm_enabled = [True for _ in queries]

print(queries[:10])

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(
        executor.map(
            retrieval_service.retrieve_documents, queries, request_ids, is_llm_enabled
        )
    )

flattened_json = [result.model_dump() for result in results]

with open("app/data/reports/retrieval_data.json", mode="w") as json_file:
    json.dump(flattened_json, json_file, indent=4)
