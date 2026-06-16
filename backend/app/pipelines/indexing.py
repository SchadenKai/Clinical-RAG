"""Indexing pipeline.

Ingests source documents (web pages and/or uploaded files) into the vector
store. Stands alone from the SDG and evaluation pipelines and communicates with
downstream stages only through the populated vector database.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.logger import app_logger
from app.services.rag import IndexingService
from app.utils import get_request_id


@dataclass(frozen=True)
class IndexingResult:
    source: str
    kind: str  # "website" | "file"
    succeeded: bool
    error: str | None = None


@dataclass(frozen=True)
class IndexingPipelineReport:
    results: tuple[IndexingResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.succeeded)

    @property
    def failed(self) -> int:
        return self.total - self.succeeded


class IndexingPipeline:
    """Indexes a batch of websites and/or object-store files."""

    def __init__(self, indexing_service: IndexingService):
        self._indexing_service = indexing_service

    @classmethod
    def from_manual(cls) -> "IndexingPipeline":
        from app.routes.dependencies.rag import get_indexing_service_manual

        return cls(indexing_service=get_indexing_service_manual())

    def run(
        self,
        website_urls: list[str] | None = None,
        file_keys: list[str] | None = None,
    ) -> IndexingPipelineReport:
        website_urls = website_urls or []
        file_keys = file_keys or []
        if not website_urls and not file_keys:
            raise ValueError(
                "IndexingPipeline.run requires at least one website_url or file_key"
            )

        results: list[IndexingResult] = [
            self._ingest_website(url) for url in website_urls
        ]
        results.extend(self._ingest_file(file_key) for file_key in file_keys)

        report = IndexingPipelineReport(results=tuple(results))
        app_logger.info(
            "Indexing pipeline done: %d succeeded / %d failed",
            report.succeeded,
            report.failed,
        )
        return report

    def _ingest_website(self, website_url: str) -> IndexingResult:
        app_logger.info("Indexing website: %s", website_url)
        try:
            self._indexing_service.ingest_website(
                website_url=website_url, request_id=get_request_id()
            )
            return IndexingResult(source=website_url, kind="website", succeeded=True)
        except Exception as e:
            # A single bad source must not abort the whole batch.
            app_logger.error("Failed to index website %s: %s", website_url, e)
            return IndexingResult(
                source=website_url, kind="website", succeeded=False, error=str(e)
            )

    def _ingest_file(self, file_key: str) -> IndexingResult:
        app_logger.info("Indexing file: %s", file_key)
        try:
            self._indexing_service.ingest_document(
                file_key=file_key, request_id=get_request_id()
            )
            return IndexingResult(source=file_key, kind="file", succeeded=True)
        except Exception as e:
            app_logger.error("Failed to index file %s: %s", file_key, e)
            return IndexingResult(
                source=file_key, kind="file", succeeded=False, error=str(e)
            )
