"""Dagster assets wrapping the standalone batch pipelines.

Lineage::

    indexed_documents ─┐
                       ├─> evaluation_report
    golden_dataset ────┘

``indexed_documents`` and ``golden_dataset`` are independent branches off the
source documents (vector DB vs golden JSON). ``evaluation_report`` depends on
both: it needs the populated vector index (to retrieve) and the golden dataset
(to score against). Assets are backed by external storage (Milvus, the object
store, the golden/report files), so they declare dependencies for ordering and
lineage and report run metadata rather than passing payloads through Dagster IO.
"""

from dagster import Config, MaterializeResult, asset

from app.data.web_sources import urls
from app.pipelines.evaluation import EvalPipeline
from app.pipelines.indexing import IndexingPipeline
from app.pipelines.sdg import SdgPipeline

GROUP = "rag"


class IndexingConfig(Config):
    # When website_urls is empty, fall back to the curated web_sources list.
    website_urls: list[str] | None = None
    file_keys: list[str] | None = None


class SdgConfig(Config):
    file_keys: list[str] | None = None
    max_goldens_per_context: int = 10


class EvalConfig(Config):
    quality_threshold: float = 0.8
    limit: int | None = None


@asset(
    group_name=GROUP,
    description="Ingest source documents into the vector store.",
)
def indexed_documents(config: IndexingConfig) -> MaterializeResult:
    report = IndexingPipeline.from_manual().run(
        website_urls=config.website_urls or urls,
        file_keys=config.file_keys,
    )
    return MaterializeResult(
        metadata={
            "total": report.total,
            "succeeded": report.succeeded,
            "failed": report.failed,
        }
    )


@asset(
    group_name=GROUP,
    description="Generate the synthetic golden dataset with deepeval.",
)
def golden_dataset(config: SdgConfig) -> MaterializeResult:
    report = SdgPipeline.from_manual().run(
        file_keys=config.file_keys,
        max_goldens_per_context=config.max_goldens_per_context,
    )
    return MaterializeResult(
        metadata={
            "golden_count": report.golden_count,
            "output_path": report.output_path,
        }
    )


@asset(
    group_name=GROUP,
    deps=[indexed_documents, golden_dataset],
    description="Score the RAG agent against the golden dataset.",
)
def evaluation_report(config: EvalConfig) -> MaterializeResult:
    report = EvalPipeline.from_manual(quality_threshold=config.quality_threshold).run(
        limit=config.limit
    )
    return MaterializeResult(
        metadata={
            "evaluated_count": report.evaluated_count,
            "total_goldens": report.total_goldens,
            "report_path": report.report_path,
        }
    )
