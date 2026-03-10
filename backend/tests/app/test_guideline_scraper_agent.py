"""
Tests for the guideline_scraper LangGraph agent:
  - Individual node functions (nodes.py)
  - Edge routing functions (edges.py)
  - End-to-end agent graph (main.py)

All external I/O (scrapper functions, S3/MinIO) is mocked.
"""

from unittest.mock import AsyncMock, patch

import pytest
from langgraph.types import Command
from pytest_mock import MockerFixture

from app.agent.guideline_scraper.context import AgentContext
from app.agent.guideline_scraper.edges import is_any_records_found, route_entry
from app.agent.guideline_scraper.models import PdfRecord, ScraperProgressEnum
from app.agent.guideline_scraper.nodes import (
    cdc_url_collector_node,
    download_and_upload_node,
    merge_records_node,
    who_url_collector_node,
)
from app.agent.guideline_scraper.state import AgentState
from app.core.config import Settings
from app.services.file_store.db import S3Service

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------


def _make_pdf_record(url: str, source: str = "who", **kwargs) -> PdfRecord:
    return PdfRecord(pdf_url=url, source=source, **kwargs)


def _make_runtime(mocker: MockerFixture, existing_keys: list[str] | None = None):
    """Return a mocked Runtime[AgentContext] with a pre-configured S3 client."""
    mock_s3_client = mocker.MagicMock()

    # Paginator mock for list_objects_v2
    mock_paginator = mocker.MagicMock()
    contents = [{"Key": k} for k in (existing_keys or [])]
    mock_paginator.paginate.return_value = (
        [{"Contents": contents}] if contents else [{}]
    )
    mock_s3_client.get_paginator.return_value = mock_paginator

    mock_s3_service = mocker.Mock(spec=S3Service)
    mock_s3_service.client = mock_s3_client

    mock_settings = mocker.Mock(spec=Settings)
    mock_settings.minio_bucket_name = "test-bucket"

    mock_context = mocker.MagicMock(spec=AgentContext)
    mock_context.s3_service = mock_s3_service
    mock_context.settings = mock_settings

    mock_runtime = mocker.MagicMock()
    mock_runtime.context = mock_context

    return mock_runtime, mock_s3_client


# ---------------------------------------------------------------------------
# TestWhoUrlCollectorNode
# ---------------------------------------------------------------------------


class TestWhoUrlCollectorNode:
    async def test_wraps_absolute_urls_as_pdf_records(self, mocker: MockerFixture):
        with patch(
            "app.agent.guideline_scraper.nodes.who_pdf_url_list",
            new_callable=AsyncMock,
            return_value={"https://www.who.int/pub/guide.pdf"},
        ):
            result = await who_url_collector_node(AgentState())

        assert len(result["who_pdf_records"]) == 1
        record = result["who_pdf_records"][0]
        assert record.source == "who"
        assert record.pdf_url == "https://www.who.int/pub/guide.pdf"
        assert result["progress_status"] == ScraperProgressEnum.COLLECTING_WHO_URLS

    async def test_prepends_host_for_relative_urls(self, mocker: MockerFixture):
        with patch(
            "app.agent.guideline_scraper.nodes.who_pdf_url_list",
            new_callable=AsyncMock,
            return_value={"/publications/i/item/guide.pdf"},
        ):
            result = await who_url_collector_node(AgentState())

        assert (
            result["who_pdf_records"][0].pdf_url
            == "https://www.who.int/publications/i/item/guide.pdf"
        )

    async def test_filters_none_and_empty_urls(self, mocker: MockerFixture):
        with patch(
            "app.agent.guideline_scraper.nodes.who_pdf_url_list",
            new_callable=AsyncMock,
            return_value={None, "", "https://www.who.int/pub/valid.pdf"},
        ):
            result = await who_url_collector_node(AgentState())

        assert len(result["who_pdf_records"]) == 1

    async def test_uses_custom_who_url_from_state(self, mocker: MockerFixture):
        custom_url = "https://www.who.int/custom-publications"
        captured = {}

        async def fake_who_pdf_url_list(url):
            captured["url"] = url
            return {"https://www.who.int/pub/guide.pdf"}

        with patch(
            "app.agent.guideline_scraper.nodes.who_pdf_url_list", fake_who_pdf_url_list
        ):
            await who_url_collector_node(AgentState(who_url=custom_url))

        assert captured["url"] == custom_url


# ---------------------------------------------------------------------------
# TestCdcUrlCollectorNode
# ---------------------------------------------------------------------------


class TestCdcUrlCollectorNode:
    async def test_short_circuits_when_scrape_cdc_false(self, mocker: MockerFixture):
        mock_oai = mocker.patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai"
        )
        mock_pw = mocker.patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_playwright"
        )

        result = await cdc_url_collector_node(AgentState(scrape_cdc=False))

        assert result["cdc_pdf_records"] == []
        mock_oai.assert_not_called()
        mock_pw.assert_not_called()

    async def test_uses_oai_results_when_available(self, mocker: MockerFixture):
        oai_data = [
            {
                "pdf_url": "https://stacks.cdc.gov/view/cdc/1/cdc_1_DS1.pdf",
                "title": "T",
                "date": "D",
                "identifier": "I",
            }
        ]
        mock_pw = mocker.patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_playwright"
        )

        with patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
            new_callable=AsyncMock,
            return_value=oai_data,
        ):
            result = await cdc_url_collector_node(AgentState(scrape_cdc=True))

        assert len(result["cdc_pdf_records"]) == 1
        assert result["cdc_pdf_records"][0].source == "cdc"
        assert result["cdc_pdf_records"][0].title == "T"
        mock_pw.assert_not_called()

    async def test_falls_back_to_playwright_when_oai_empty(self, mocker: MockerFixture):
        pw_data = [
            {
                "pdf_url": "https://stacks.cdc.gov/guidelines/doc.pdf",
                "title": "Doc",
                "page_url": "https://stacks.cdc.gov",
            }
        ]

        with patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_playwright",
                new_callable=AsyncMock,
                return_value=pw_data,
            ):
                result = await cdc_url_collector_node(AgentState(scrape_cdc=True))

        assert len(result["cdc_pdf_records"]) == 1

    async def test_filters_records_missing_pdf_url(self, mocker: MockerFixture):
        oai_data = [
            {"pdf_url": "https://stacks.cdc.gov/view/cdc/1/cdc_1_DS1.pdf"},
            {"title": "No URL record"},  # missing pdf_url
        ]

        with patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
            new_callable=AsyncMock,
            return_value=oai_data,
        ):
            result = await cdc_url_collector_node(AgentState(scrape_cdc=True))

        assert len(result["cdc_pdf_records"]) == 1

    async def test_returns_collecting_cdc_urls_status(self, mocker: MockerFixture):
        with patch(
            "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
            new_callable=AsyncMock,
            return_value=[
                {"pdf_url": "https://stacks.cdc.gov/view/cdc/1/cdc_1_DS1.pdf"}
            ],
        ):
            result = await cdc_url_collector_node(AgentState(scrape_cdc=True))

        assert result["progress_status"] == ScraperProgressEnum.COLLECTING_CDC_URLS


# ---------------------------------------------------------------------------
# TestMergeRecordsNode
# ---------------------------------------------------------------------------


class TestMergeRecordsNode:
    def test_merges_who_and_cdc_records(self):
        state = AgentState(
            scrape_who=True,
            scrape_cdc=True,
            who_pdf_records=[
                _make_pdf_record("https://who.int/a.pdf", "who"),
                _make_pdf_record("https://who.int/b.pdf", "who"),
            ],
            cdc_pdf_records=[
                _make_pdf_record("https://cdc.gov/c.pdf", "cdc"),
                _make_pdf_record("https://cdc.gov/d.pdf", "cdc"),
            ],
        )
        result = merge_records_node(state)
        assert len(result["all_pdf_records"]) == 4

    def test_deduplicates_by_pdf_url(self):
        shared_url = "https://example.com/shared.pdf"
        state = AgentState(
            scrape_who=True,
            scrape_cdc=True,
            who_pdf_records=[
                _make_pdf_record(shared_url, "who"),
                _make_pdf_record("https://who.int/unique.pdf", "who"),
            ],
            cdc_pdf_records=[
                _make_pdf_record(shared_url, "cdc"),  # duplicate
                _make_pdf_record("https://cdc.gov/other.pdf", "cdc"),
            ],
        )
        result = merge_records_node(state)
        assert len(result["all_pdf_records"]) == 3

    def test_respects_scrape_who_false(self):
        state = AgentState(
            scrape_who=False,
            scrape_cdc=True,
            who_pdf_records=[_make_pdf_record("https://who.int/a.pdf", "who")],
            cdc_pdf_records=[_make_pdf_record("https://cdc.gov/b.pdf", "cdc")],
        )
        result = merge_records_node(state)
        assert len(result["all_pdf_records"]) == 1
        assert result["all_pdf_records"][0].source == "cdc"

    def test_respects_scrape_cdc_false(self):
        state = AgentState(
            scrape_who=True,
            scrape_cdc=False,
            who_pdf_records=[_make_pdf_record("https://who.int/a.pdf", "who")],
            cdc_pdf_records=[_make_pdf_record("https://cdc.gov/b.pdf", "cdc")],
        )
        result = merge_records_node(state)
        assert len(result["all_pdf_records"]) == 1
        assert result["all_pdf_records"][0].source == "who"

    def test_returns_empty_when_no_records(self):
        state = AgentState(scrape_who=True, scrape_cdc=True)
        result = merge_records_node(state)
        assert result["all_pdf_records"] == []

    def test_status_is_merging_records(self):
        state = AgentState(
            scrape_who=True,
            scrape_cdc=True,
            who_pdf_records=[_make_pdf_record("https://who.int/a.pdf", "who")],
        )
        result = merge_records_node(state)
        assert result["progress_status"] == ScraperProgressEnum.MERGING_RECORDS


# ---------------------------------------------------------------------------
# TestDownloadAndUploadNode
# ---------------------------------------------------------------------------


class TestDownloadAndUploadNode:
    async def test_uploads_pdf_to_minio(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(mocker, existing_keys=[])
        state = AgentState(
            all_pdf_records=[_make_pdf_record("https://who.int/pub/guide.pdf", "who")]
        )

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
            return_value=b"%PDF test",
        ):
            result = await download_and_upload_node(state, runtime)

        assert result["uploaded_keys"] == ["raw-pdfs/who/guide.pdf"]
        assert result["failed_urls"] == []
        assert result["skipped_urls"] == []
        s3_client.upload_fileobj.assert_called_once()

    async def test_upload_uses_correct_content_type(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(mocker)
        state = AgentState(
            all_pdf_records=[_make_pdf_record("https://who.int/pub/guide.pdf", "who")]
        )

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
            return_value=b"%PDF test",
        ):
            await download_and_upload_node(state, runtime)

        call_kwargs = s3_client.upload_fileobj.call_args[1]
        assert call_kwargs.get("ExtraArgs") == {"ContentType": "application/pdf"}

    async def test_skips_existing_minio_key(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(
            mocker, existing_keys=["raw-pdfs/who/guide.pdf"]
        )
        state = AgentState(
            all_pdf_records=[_make_pdf_record("https://who.int/pub/guide.pdf", "who")]
        )

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
        ) as mock_dl:
            result = await download_and_upload_node(state, runtime)

        assert result["skipped_urls"] == ["https://who.int/pub/guide.pdf"]
        assert result["uploaded_keys"] == []
        mock_dl.assert_not_called()
        s3_client.upload_fileobj.assert_not_called()

    async def test_records_failed_url_on_download_failure(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(mocker)
        state = AgentState(
            all_pdf_records=[_make_pdf_record("https://who.int/pub/guide.pdf", "who")]
        )

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
            return_value=None,  # download failed
        ):
            result = await download_and_upload_node(state, runtime)

        assert result["failed_urls"] == ["https://who.int/pub/guide.pdf"]
        assert result["uploaded_keys"] == []
        s3_client.upload_fileobj.assert_not_called()

    async def test_records_failed_url_on_upload_error(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(mocker)
        s3_client.upload_fileobj.side_effect = Exception("MinIO unavailable")
        state = AgentState(
            all_pdf_records=[_make_pdf_record("https://who.int/pub/guide.pdf", "who")]
        )

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
            return_value=b"%PDF test",
        ):
            result = await download_and_upload_node(state, runtime)

        assert result["failed_urls"] == ["https://who.int/pub/guide.pdf"]
        assert result["uploaded_keys"] == []

    async def test_run_metadata_counts_are_accurate(self, mocker: MockerFixture):
        # 3 records: 1 success, 1 skip (pre-existing), 1 fail (download returns None)
        runtime, s3_client = _make_runtime(
            mocker, existing_keys=["raw-pdfs/cdc/skip.pdf"]
        )
        state = AgentState(
            all_pdf_records=[
                _make_pdf_record("https://who.int/success.pdf", "who"),
                _make_pdf_record(
                    "https://stacks.cdc.gov/skip.pdf", "cdc"
                ),  # key = raw-pdfs/cdc/skip.pdf
                _make_pdf_record("https://who.int/fail.pdf", "who"),
            ]
        )

        def fake_download(url, **kwargs):
            if "fail" in url:
                return None
            return b"%PDF test"

        with patch(
            "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
            new_callable=AsyncMock,
            side_effect=fake_download,
        ):
            result = await download_and_upload_node(state, runtime)

        meta = result["run_metadata"]
        assert meta["total_records"] == 3
        assert meta["uploaded"] == 1
        assert meta["skipped"] == 1
        assert meta["failed"] == 1

    async def test_handles_empty_all_pdf_records(self, mocker: MockerFixture):
        runtime, s3_client = _make_runtime(mocker)
        state = AgentState(all_pdf_records=[])

        result = await download_and_upload_node(state, runtime)

        assert result["uploaded_keys"] == []
        assert result["failed_urls"] == []
        assert result["skipped_urls"] == []
        s3_client.upload_fileobj.assert_not_called()

    async def test_status_is_done(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)
        state = AgentState(all_pdf_records=[])

        result = await download_and_upload_node(state, runtime)

        assert result["progress_status"] == ScraperProgressEnum.DONE


# ---------------------------------------------------------------------------
# TestDeriveFilename
# ---------------------------------------------------------------------------


class TestDeriveFilename:
    """Tests for the _derive_filename private helper in nodes.py."""

    def test_normal_url_uses_last_path_segment(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        record = _make_pdf_record("https://who.int/pub/guidelines/cardiac-care.pdf")
        assert _derive_filename(record) == "cardiac-care.pdf"

    def test_appends_pdf_suffix_when_missing(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        record = _make_pdf_record("https://who.int/pub/guidelines/cardiac-care")
        result = _derive_filename(record)
        assert result.endswith(".pdf")

    def test_fallback_for_empty_path(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        # URL with no path segment at all — path resolves to ""
        record = _make_pdf_record("https://stacks.cdc.gov")
        result = _derive_filename(record)
        assert result.endswith(".pdf")
        assert not result.startswith(".")
        assert len(result) > len(".pdf")

    def test_fallback_for_root_path(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        # URL whose path is exactly "/" — last segment after rstrip is ""
        record = _make_pdf_record("https://stacks.cdc.gov/")
        result = _derive_filename(record)
        assert result.endswith(".pdf")
        assert not result.startswith(".")

    def test_fallback_is_deterministic(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        record = _make_pdf_record("https://stacks.cdc.gov/")
        assert _derive_filename(record) == _derive_filename(record)

    def test_sanitizes_special_characters(self):
        from app.agent.guideline_scraper.nodes import _derive_filename

        record = _make_pdf_record("https://who.int/pub/guide line (2024).pdf")
        result = _derive_filename(record)
        assert " " not in result
        assert "(" not in result
        assert ")" not in result


# ---------------------------------------------------------------------------
# TestGuidelineScraperEdges
# ---------------------------------------------------------------------------


class TestGuidelineScraperEdges:
    def test_route_entry_goes_to_who_when_scrape_who_true(self):
        result = route_entry(AgentState(scrape_who=True))
        assert result == "who_url_collector_node"

    def test_route_entry_goes_to_cdc_when_scrape_who_false(self):
        result = route_entry(AgentState(scrape_who=False))
        assert result == "cdc_url_collector_node"

    def test_is_any_records_found_routes_to_download_when_records_exist(self):
        state = AgentState(all_pdf_records=[_make_pdf_record("https://who.int/a.pdf")])
        cmd: Command = is_any_records_found(state)
        assert cmd.goto == "download_and_upload_node"

    def test_is_any_records_found_ends_when_no_records(self):
        state = AgentState(all_pdf_records=[])
        cmd: Command = is_any_records_found(state)
        assert cmd.goto == "__end__"

    def test_is_any_records_found_ends_when_records_is_none(self):
        state = AgentState(all_pdf_records=None)
        cmd: Command = is_any_records_found(state)
        assert cmd.goto == "__end__"

    def test_is_any_records_found_sets_done_status_on_early_exit(self):
        state = AgentState(all_pdf_records=[])
        cmd: Command = is_any_records_found(state)
        assert cmd.update.get("progress_status") == ScraperProgressEnum.DONE

    def test_is_any_records_found_sets_error_metadata_on_early_exit(self):
        state = AgentState(all_pdf_records=None)
        cmd: Command = is_any_records_found(state)
        assert "error" in cmd.update.get("run_metadata", {})


# ---------------------------------------------------------------------------
# TestGuidelineScraperAgentIntegration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestGuidelineScraperAgentIntegration:
    @pytest.fixture
    def agent_context(self, mocker: MockerFixture) -> AgentContext:
        mock_s3_client = mocker.MagicMock()
        mock_paginator = mocker.MagicMock()
        mock_paginator.paginate.return_value = [{}]  # no existing keys
        mock_s3_client.get_paginator.return_value = mock_paginator

        mock_s3_service = mocker.Mock(spec=S3Service)
        mock_s3_service.client = mock_s3_client

        mock_settings = mocker.Mock(spec=Settings)
        mock_settings.minio_bucket_name = "test-bucket"

        return AgentContext(s3_service=mock_s3_service, settings=mock_settings)

    async def test_agent_full_run_who_and_cdc(self, agent_context: AgentContext):
        from app.agent.guideline_scraper.main import agent

        who_data = {"https://www.who.int/pub/guide.pdf"}
        cdc_data = [
            {
                "pdf_url": "https://stacks.cdc.gov/view/cdc/1/cdc_1_DS1.pdf",
                "title": "CDC Guide",
            }
        ]

        with (
            patch(
                "app.agent.guideline_scraper.nodes.who_pdf_url_list",
                new_callable=AsyncMock,
                return_value=who_data,
            ),
            patch(
                "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
                new_callable=AsyncMock,
                return_value=cdc_data,
            ),
            patch(
                "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
                new_callable=AsyncMock,
                return_value=b"%PDF",
            ),
        ):
            final_state = {}
            config = {"configurable": {"thread_id": "test-full-run"}}
            async for chunk in agent.astream(
                input=AgentState(scrape_who=True, scrape_cdc=True),
                context=agent_context,
                config=config,
            ):
                for _, state in chunk.items():
                    final_state = state

        assert "uploaded_keys" in final_state or "run_metadata" in final_state

    async def test_agent_only_cdc(self, agent_context: AgentContext):
        from app.agent.guideline_scraper.main import agent

        cdc_data = [{"pdf_url": "https://stacks.cdc.gov/view/cdc/1/cdc_1_DS1.pdf"}]

        with (
            patch(
                "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
                new_callable=AsyncMock,
                return_value=cdc_data,
            ),
            patch(
                "app.agent.guideline_scraper.nodes.download_pdf_to_bytes",
                new_callable=AsyncMock,
                return_value=b"%PDF",
            ),
        ):
            node_names_visited = []
            config = {"configurable": {"thread_id": "test-cdc-only"}}
            async for chunk in agent.astream(
                input=AgentState(scrape_who=False, scrape_cdc=True),
                context=agent_context,
                config=config,
            ):
                node_names_visited.extend(chunk.keys())

        assert "who_url_collector_node" not in node_names_visited
        assert "cdc_url_collector_node" in node_names_visited

    async def test_agent_aborts_when_no_records(self, agent_context: AgentContext):
        from app.agent.guideline_scraper.main import agent

        with (
            patch(
                "app.agent.guideline_scraper.nodes.who_pdf_url_list",
                new_callable=AsyncMock,
                return_value=set(),
            ),
            patch(
                "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_oai",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "app.agent.guideline_scraper.nodes.cdc_pdf_url_list_playwright",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            node_names_visited = []
            final_state = {}
            config = {"configurable": {"thread_id": "test-no-records"}}
            async for chunk in agent.astream(
                input=AgentState(scrape_who=True, scrape_cdc=True),
                context=agent_context,
                config=config,
            ):
                node_names_visited.extend(chunk.keys())
                for _, state in chunk.items():
                    final_state = state

        # download_and_upload_node must NOT be visited
        assert "download_and_upload_node" not in node_names_visited
        # is_any_records_found provides the early exit with error metadata
        assert "is_any_records_found" in node_names_visited
        assert "error" in final_state.get("run_metadata", {})
