"""
Tests for the 3 new scrapper functions added to app/services/scrapper.py:
  - cdc_pdf_url_list_oai
  - cdc_pdf_url_list_playwright
  - download_pdf_to_bytes

All external I/O (httpx, playwright) is mocked so tests run without
network access or a running browser.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _oai_xml(records: list[dict], resumption_token: str | None = None) -> str:
    """Build a minimal OAI-PMH ListRecords XML response for testing."""
    record_blocks = ""
    for r in records:
        status_attr = f' status="{r["status"]}"' if r.get("status") else ""
        record_blocks += f"""
        <record>
          <header{status_attr}>
            <identifier>{r.get("identifier", "oai:stacks.cdc.gov:cdc/999")}</identifier>
          </header>
          <metadata>
            <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                       xmlns:dc="http://purl.org/dc/elements/1.1/">
              <dc:title>{r.get("title", "Test Title")}</dc:title>
              <dc:date>{r.get("date", "2024-01-01")}</dc:date>
            </oai_dc:dc>
          </metadata>
        </record>"""

    token_block = (
        f"<resumptionToken>{resumption_token}</resumptionToken>"
        if resumption_token
        else "<resumptionToken/>"
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords>
    {record_blocks}
    {token_block}
  </ListRecords>
</OAI-PMH>"""


def _make_httpx_response(text: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# TestCdcPdfUrlListOai
# ---------------------------------------------------------------------------


class TestCdcPdfUrlListOai:
    # httpx and asyncio are imported locally inside cdc_pdf_url_list_oai,
    # so we patch at the real module level ("httpx.AsyncClient", "asyncio.sleep").

    def test_returns_records_with_pdf_url_and_metadata(self):
        from app.services.scrapper import cdc_pdf_url_list_oai

        xml = _oai_xml(
            [
                {
                    "identifier": "oai:stacks.cdc.gov:cdc/12345",
                    "title": "Guide A",
                    "date": "2024-01",
                },
                {
                    "identifier": "oai:stacks.cdc.gov:cdc/67890",
                    "title": "Guide B",
                    "date": "2023-06",
                },
            ]
        )

        mock_resp = _make_httpx_response(xml)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            results = asyncio.run(cdc_pdf_url_list_oai())

        assert len(results) == 2
        r = results[0]
        assert "pdf_url" in r
        assert "title" in r
        assert "date" in r
        assert "cdc_id" in r
        assert "12345" in r["pdf_url"]
        assert "cdc_12345_DS1.pdf" in r["pdf_url"]

    def test_skips_deleted_records(self):
        from app.services.scrapper import cdc_pdf_url_list_oai

        xml = _oai_xml(
            [
                {"identifier": "oai:stacks.cdc.gov:cdc/111", "status": "deleted"},
                {"identifier": "oai:stacks.cdc.gov:cdc/222"},
            ]
        )

        mock_resp = _make_httpx_response(xml)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            results = asyncio.run(cdc_pdf_url_list_oai())

        assert len(results) == 1
        assert "222" in results[0]["pdf_url"]

    def test_stops_fetching_pages_when_max_records_reached(self):
        """
        max_records is a page-level guard: once the accumulated count meets
        the threshold after finishing a page, no further pages are fetched.
        It does NOT truncate within a page, so the final count may be >= max_records.
        """
        from app.services.scrapper import cdc_pdf_url_list_oai

        # Page 1: 3 records + resumptionToken (would normally trigger page 2)
        page1_records = [
            {"identifier": f"oai:stacks.cdc.gov:cdc/{i}"} for i in range(1, 4)
        ]
        page1_xml = _oai_xml(page1_records, resumption_token="tok-next")

        # Page 2: should NOT be fetched once max_records=3 is satisfied after page 1
        page2_xml = _oai_xml([{"identifier": "oai:stacks.cdc.gov:cdc/99"}])

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                _make_httpx_response(page1_xml),
                _make_httpx_response(page2_xml),
            ]
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                results = asyncio.run(cdc_pdf_url_list_oai(max_records=3))

        # Exactly the 3 records from page 1 — page 2 was never requested
        assert len(results) == 3
        assert mock_client.get.call_count == 1

    def test_paginates_until_no_resumption_token(self):
        from app.services.scrapper import cdc_pdf_url_list_oai

        page1_xml = _oai_xml(
            [
                {"identifier": "oai:stacks.cdc.gov:cdc/1"},
                {"identifier": "oai:stacks.cdc.gov:cdc/2"},
            ],
            resumption_token="tok-abc",
        )
        page2_xml = _oai_xml(
            [{"identifier": "oai:stacks.cdc.gov:cdc/3"}],
            resumption_token=None,
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                _make_httpx_response(page1_xml),
                _make_httpx_response(page2_xml),
            ]
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                results = asyncio.run(cdc_pdf_url_list_oai())

        assert len(results) == 3
        assert mock_client.get.call_count == 2

    def test_returns_partial_results_on_malformed_xml(self):
        """
        When a page returns malformed XML, the function breaks out of the loop
        and returns whatever records were collected on previous pages — it must
        not raise ET.ParseError to the caller.
        """
        from app.services.scrapper import cdc_pdf_url_list_oai

        page1_xml = _oai_xml(
            [{"identifier": "oai:stacks.cdc.gov:cdc/1"}],
            resumption_token="tok-bad",
        )
        bad_xml_resp = _make_httpx_response("<broken xml <<< not valid")
        bad_xml_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                _make_httpx_response(page1_xml),
                bad_xml_resp,
            ]
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                results = asyncio.run(cdc_pdf_url_list_oai())

        # Returns the 1 record from page 1; does not raise
        assert len(results) == 1
        assert "1" in results[0]["pdf_url"]

    def test_resumption_token_params_exclude_metadata_prefix(self):
        from app.services.scrapper import cdc_pdf_url_list_oai

        page1_xml = _oai_xml(
            [{"identifier": "oai:stacks.cdc.gov:cdc/1"}],
            resumption_token="tok-xyz",
        )
        page2_xml = _oai_xml(
            [{"identifier": "oai:stacks.cdc.gov:cdc/2"}],
            resumption_token=None,
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                _make_httpx_response(page1_xml),
                _make_httpx_response(page2_xml),
            ]
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                asyncio.run(cdc_pdf_url_list_oai())

        # Second call must use only resumptionToken — no metadataPrefix
        second_call_kwargs = mock_client.get.call_args_list[1]
        params = second_call_kwargs[1].get("params") or second_call_kwargs[0][1]
        assert "resumptionToken" in params
        assert "metadataPrefix" not in params

    def test_raises_on_http_error(self):
        import httpx
        from app.services.scrapper import cdc_pdf_url_list_oai

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("server error"))

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with pytest.raises(httpx.HTTPError):
                asyncio.run(cdc_pdf_url_list_oai())


# ---------------------------------------------------------------------------
# TestCdcPdfUrlListPlaywright
# ---------------------------------------------------------------------------


class TestCdcPdfUrlListPlaywright:
    def _make_playwright_mocks(
        self,
        pages_links: list[list[dict]],
        next_btn_states: list[tuple[bool, bool]],  # (is_visible, is_disabled) per check
    ) -> tuple[MagicMock, MagicMock]:
        """
        Build async mock objects for async_playwright context.

        pages_links: list of link-lists, one per page.evaluate call.
        next_btn_states: (is_visible, is_disabled) pairs, one per loop iteration.
        """
        # page.evaluate returns successive page results
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=pages_links)

        # Build next_btn mock that cycles through states
        mock_next_btn = AsyncMock()
        visible_seq = [v for v, _ in next_btn_states]
        disabled_seq = [d for _, d in next_btn_states]
        mock_next_btn.is_visible = AsyncMock(side_effect=visible_seq)
        mock_next_btn.is_disabled = AsyncMock(side_effect=disabled_seq)
        mock_next_btn.click = AsyncMock()

        mock_page.locator = MagicMock(return_value=MagicMock(first=mock_next_btn))

        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = AsyncMock()
        mock_playwright.chromium = mock_chromium

        return mock_playwright, mock_page

    def test_collects_pdf_links_across_pages(self):
        from app.services.scrapper import cdc_pdf_url_list_playwright

        page1_links = [
            {
                "pdf_url": "https://example.com/a.pdf",
                "title": "A",
                "page_url": "https://example.com/p1",
            },
            {
                "pdf_url": "https://example.com/b.pdf",
                "title": "B",
                "page_url": "https://example.com/p1",
            },
        ]
        page2_links = [
            {
                "pdf_url": "https://example.com/c.pdf",
                "title": "C",
                "page_url": "https://example.com/p2",
            },
        ]
        mock_playwright, _ = self._make_playwright_mocks(
            pages_links=[page1_links, page2_links],
            # First check: visible+enabled (proceed to page 2)
            # Second check: not visible (stop)
            next_btn_states=[(True, False), (False, True)],
        )

        with patch("app.services.scrapper.async_playwright") as mock_ap:
            mock_ap.return_value.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_ap.return_value.__aexit__ = AsyncMock(return_value=False)
            results = asyncio.run(cdc_pdf_url_list_playwright())

        assert len(results) == 3
        urls = {r["pdf_url"] for r in results}
        assert urls == {
            "https://example.com/a.pdf",
            "https://example.com/b.pdf",
            "https://example.com/c.pdf",
        }

    def test_deduplicates_pdf_links(self):
        from app.services.scrapper import cdc_pdf_url_list_playwright

        same_link = {
            "pdf_url": "https://example.com/dup.pdf",
            "title": "Dup",
            "page_url": "https://example.com",
        }
        mock_playwright, _ = self._make_playwright_mocks(
            pages_links=[[same_link], [same_link]],
            next_btn_states=[(True, False), (False, True)],
        )

        with patch("app.services.scrapper.async_playwright") as mock_ap:
            mock_ap.return_value.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_ap.return_value.__aexit__ = AsyncMock(return_value=False)
            results = asyncio.run(cdc_pdf_url_list_playwright())

        assert len(results) == 1

    def test_stops_when_no_next_button(self):
        from app.services.scrapper import cdc_pdf_url_list_playwright

        page1_links = [
            {
                "pdf_url": "https://example.com/only.pdf",
                "title": "Only",
                "page_url": "https://example.com",
            }
        ]
        mock_playwright, _ = self._make_playwright_mocks(
            pages_links=[page1_links],
            # Immediately not visible → stop after first page
            next_btn_states=[(False, True)],
        )

        with patch("app.services.scrapper.async_playwright") as mock_ap:
            mock_ap.return_value.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_ap.return_value.__aexit__ = AsyncMock(return_value=False)
            results = asyncio.run(cdc_pdf_url_list_playwright())

        assert len(results) == 1


# ---------------------------------------------------------------------------
# TestDownloadPdfToBytes
# ---------------------------------------------------------------------------


class TestDownloadPdfToBytes:
    # httpx is imported locally inside download_pdf_to_bytes, so we patch
    # at the real module level ("httpx.AsyncClient").

    def _make_response(
        self,
        content: bytes = b"%PDF-1.4 test content",
        content_type: str = "application/pdf",
        status_code: int = 200,
    ) -> AsyncMock:
        resp = AsyncMock()
        resp.content = content
        resp.headers = {"content-type": content_type}
        resp.raise_for_status = MagicMock()
        return resp

    def test_returns_bytes_for_pdf_content_type(self):
        from app.services.scrapper import download_pdf_to_bytes

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._make_response())

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = asyncio.run(download_pdf_to_bytes("https://example.com/guide.pdf"))

        assert result == b"%PDF-1.4 test content"

    def test_returns_bytes_when_url_ends_in_pdf_regardless_of_content_type(self):
        from app.services.scrapper import download_pdf_to_bytes

        # Some servers return octet-stream; URL ending in .pdf is sufficient
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=self._make_response(content_type="application/octet-stream")
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = asyncio.run(download_pdf_to_bytes("https://example.com/guide.pdf"))

        assert result is not None

    def test_returns_none_for_non_pdf_content_type_and_non_pdf_url(self):
        from app.services.scrapper import download_pdf_to_bytes

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=self._make_response(content_type="text/html")
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            # URL does not end in .pdf either
            result = asyncio.run(download_pdf_to_bytes("https://example.com/page"))

        assert result is None

    def test_returns_none_on_exception(self):
        from app.services.scrapper import download_pdf_to_bytes

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = asyncio.run(download_pdf_to_bytes("https://example.com/guide.pdf"))

        assert result is None

    def test_client_created_with_follow_redirects(self):
        from app.services.scrapper import download_pdf_to_bytes

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._make_response())

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            asyncio.run(download_pdf_to_bytes("https://example.com/guide.pdf"))

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("follow_redirects") is True
