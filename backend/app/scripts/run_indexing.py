"""Run the indexing pipeline over the configured web sources.

Usage:
    cd backend && uv run python -m app.scripts.run_indexing
"""

from app.data.web_sources import urls
from app.logger import app_logger
from app.pipelines.indexing import IndexingPipeline


def main() -> None:
    report = IndexingPipeline.from_manual().run(website_urls=urls)
    app_logger.info(
        "Indexing done: %d sources, %d succeeded, %d failed",
        report.total,
        report.succeeded,
        report.failed,
    )


if __name__ == "__main__":
    main()
