import pytest
from pytest_mock import MockerFixture, MockType

from app.pipelines.indexing import IndexingPipeline
from app.services.rag import IndexingService


def _make_pipeline(mocker: MockerFixture) -> tuple[IndexingPipeline, MockType]:
    mk_service: MockType = mocker.Mock(spec=IndexingService)
    return IndexingPipeline(indexing_service=mk_service), mk_service


class TestIndexingPipeline:
    def test_run_requires_at_least_one_source(self, mocker: MockerFixture):
        pipeline, _ = _make_pipeline(mocker)
        with pytest.raises(ValueError):
            pipeline.run()

    def test_run_indexes_each_website(self, mocker: MockerFixture):
        pipeline, mk_service = _make_pipeline(mocker)

        report = pipeline.run(website_urls=["https://a.com", "https://b.com"])

        assert mk_service.ingest_website.call_count == 2
        assert report.total == 2
        assert report.succeeded == 2
        assert report.failed == 0
        assert all(r.kind == "website" for r in report.results)

    def test_run_indexes_each_file(self, mocker: MockerFixture):
        pipeline, mk_service = _make_pipeline(mocker)

        report = pipeline.run(file_keys=["uploads/a.pdf"])

        mk_service.ingest_document.assert_called_once()
        assert report.total == 1
        assert report.results[0].kind == "file"

    def test_per_source_failure_is_captured_and_batch_continues(
        self, mocker: MockerFixture
    ):
        pipeline, mk_service = _make_pipeline(mocker)
        mk_service.ingest_website.side_effect = [
            RuntimeError("boom"),
            None,
        ]

        report = pipeline.run(website_urls=["https://bad.com", "https://ok.com"])

        assert report.total == 2
        assert report.succeeded == 1
        assert report.failed == 1
        failed = next(r for r in report.results if not r.succeeded)
        assert failed.source == "https://bad.com"
        assert failed.error == "boom"
