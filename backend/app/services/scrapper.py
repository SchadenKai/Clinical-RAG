import asyncio
import xml.etree.ElementTree as ET

import httpx
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
    JsonCssExtractionStrategy,
)
from playwright.async_api import async_playwright

from app.logger import app_logger


async def simple_crawler(url: str) -> CrawlResult:
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Tag exclusions
        excluded_tags=[
            "form",
            "header",
            "footer",
            "nav",
            "a",
        ],
        target_elements=[
            "h1",
            "h2",
            "div.date",
            "article",
        ],
        exclude_all_images=True,
        # Link filtering
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_internal_links=True,
        # Block entire domains
        exclude_domains=["adtrackers.com", "spammynews.org"],
        exclude_social_media_domains=["facebook.com", "twitter.com"],
        # Media filtering
        exclude_external_images=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        res = await crawler.arun(url=url, config=run_config)
        return res


async def who_pdf_url_list(website_url: str) -> set:
    pdf_download_url = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(website_url)

        while True:
            app_logger.debug("Gathering button hrefs")
            buttons_href: list[str | None] | None = await page.get_by_label(
                "Download"
            ).evaluate_all("el => el.map(e => e.getAttribute('href')).filter(h => h)")

            if buttons_href is None or buttons_href == []:
                next_page_btn = page.get_by_label("Go to the next page").first
                app_logger.debug("Navigating to the next page")
                if (
                    not await next_page_btn.is_visible()
                    and await next_page_btn.is_disabled()
                ):
                    app_logger.debug("Exiting")
                    break
                await next_page_btn.click()

            pdf_download_url.update(buttons_href)

            next_page_btn = page.get_by_label("Go to the next page").first
            app_logger.debug("Navigating to the next page")
            if (
                not await next_page_btn.is_visible()
                and await next_page_btn.is_disabled()
            ):
                app_logger.debug("Exiting")
                break
            await next_page_btn.click()
            await page.wait_for_load_state("domcontentloaded")

        await browser.close()
    return pdf_download_url


async def who_pdf_list_scrapper(website_url: str) -> None:
    browser_config = BrowserConfig()
    who_guidelines = {
        "name": "WHO Guidelines",
        "baseSelector": "div.sf-publications-list",
        "fields": [
            {
                "name": "files",
                "selector": "div.sf-publications-item",
                "type": "list",
                "fields": [
                    {
                        "name": "title",
                        "selector": "h3",
                        "type": "text",
                    },
                    {
                        "name": "publishing_date",
                        "selector": "div.sf-publications-item__date",
                        "type": "text",
                    },
                    {
                        "name": "a.page-url",
                        "selector": "div.sf-publications-item__header a",
                        "type": "attribute",
                        "attribute": "href",
                    },
                    {
                        "name": "pdf_link",
                        "selector": "a.download-url",
                        "type": "attribute",
                        "attribute": "href",
                    },
                ],
            }
        ],
    }
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema=who_guidelines),
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        response: CrawlResult = await crawler.arun(url=website_url, config=run_config)
        return response.extracted_content


async def structured_output_scrapper(url: str) -> CrawlResult:
    cdc_news_schema = {
        "name": "CDC Article",
        "baseSelector": "main.container",
        "fields": [
            {
                "name": "title",
                "selector": "h1",
                "type": "text",
            },
            {"name": "date", "selector": "span.date-long", "type": "text"},
            {
                "name": "page_content",
                "selector": "div[data-section='cdc_news_body']",
                "type": "text",
            },
        ],
    }
    cdc_schema = {
        "name": "CDC Article",
        "baseSelector": "main",
        "fields": [
            {
                "name": "title",
                "selector": "h1",
                "type": "text",
            },
            {"name": "date", "selector": "time", "type": "text"},
            {
                "name": "page_content",
                "selector": "div.cdc-dfe-body__center ",
                "type": "text",
            },
        ],
    }
    who_schema = {
        "name": "WHO Article",
        "baseSelector": "section.content",
        "fields": [
            {
                "name": "title",
                "selector": "h1",
                "type": "text",
            },
            {"name": "date", "selector": "span.timestamp", "type": "text"},
            {
                "name": "tags",
                "selector": "div.sf-tags-list",
                "type": "list",
                "fields": [
                    {
                        "name": "name",
                        "selector": "div.sf-tags-list-item",
                        "type": "text",
                    }
                ],
            },
            {
                "name": "page_content",
                "selector": "article",
                "type": "text",
            },
        ],
    }

    schema = None
    if "who" in url:
        schema = who_schema
    elif "/media/release" in url:
        schema = cdc_news_schema
    else:
        schema = cdc_schema

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Tag exclusions
        excluded_tags=[
            "form",
            "header",
            "footer",
            "nav",
            "a",
        ],
        target_elements=[
            "h1",
            "h2",
            "div.date",
            "article",
        ],
        exclude_all_images=True,
        # Link filtering
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_internal_links=True,
        # Block entire domains
        exclude_domains=["adtrackers.com", "spammynews.org"],
        exclude_social_media_domains=["facebook.com", "twitter.com"],
        # Media filtering
        exclude_external_images=True,
        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        res = await crawler.arun(url=url, config=run_config)
        return res


async def cdc_pdf_url_list_oai(
    base_url: str = "https://stacks.cdc.gov/fedora/oai",
    max_records: int | None = None,
) -> list[dict]:
    """
    Harvest CDC STACKS guideline metadata using the OAI-PMH protocol.

    Paginates using resumptionToken until all records are fetched.
    Constructs a direct PDF URL for each record using the CDC ID.

    Returns a list of dicts with keys:
        pdf_url, title, date, identifier, cdc_id
    """
    OAI_NS = "http://www.openarchives.org/OAI/2.0/"
    DC_NS = "http://purl.org/dc/elements/1.1/"

    records = []
    params: dict = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                resp = await client.get(base_url, params=params)
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
            except httpx.HTTPError:
                raise
            except ET.ParseError as exc:
                app_logger.error(
                    "Malformed XML from OAI-PMH endpoint: %s | status=%s | base_url=%s | "
                    "params=%s | body_preview=%.200r",
                    exc, resp.status_code, base_url, params, resp.text,
                )
                break

            for record in root.findall(f".//{{{OAI_NS}}}record"):
                header = record.find(f"{{{OAI_NS}}}header")
                if header is not None and header.get("status") == "deleted":
                    continue

                identifier_el = (
                    header.find(f"{{{OAI_NS}}}identifier")
                    if header is not None
                    else None
                )
                identifier = identifier_el.text if identifier_el is not None else ""

                # Extract numeric CDC ID from identifier like "oai:stacks.cdc.gov:cdc/12345"
                cdc_id = None
                if identifier:
                    parts = identifier.split("/")
                    if parts:
                        cdc_id = parts[-1].strip()

                metadata_el = record.find(f".//{{{OAI_NS}}}metadata")
                title, date = None, None
                if metadata_el is not None:
                    title_el = metadata_el.find(f".//{{{DC_NS}}}title")
                    title = title_el.text if title_el is not None else None
                    date_el = metadata_el.find(f".//{{{DC_NS}}}date")
                    date = date_el.text if date_el is not None else None

                if cdc_id:
                    pdf_url = (
                        f"https://stacks.cdc.gov/view/cdc/{cdc_id}/cdc_{cdc_id}_DS1.pdf"
                    )
                    records.append(
                        {
                            "pdf_url": pdf_url,
                            "title": title,
                            "identifier": identifier,
                            "date": date,
                            "cdc_id": cdc_id,
                        }
                    )

            if max_records is not None and max_records > 0 and len(records) >= max_records:
                records = records[:max_records]
                break

            token_el = root.find(f".//{{{OAI_NS}}}resumptionToken")
            if token_el is None or not token_el.text:
                break

            # resumptionToken is self-contained — do not include metadataPrefix
            params = {"verb": "ListRecords", "resumptionToken": token_el.text}
            await asyncio.sleep(0.5)

    return records


async def cdc_pdf_url_list_playwright(
    website_url: str = "https://stacks.cdc.gov/guidelines",
) -> list[dict]:
    """
    Playwright-based fallback scraper for CDC STACKS guidelines listing page.
    Collects all PDF anchor links across paginated results.

    Returns a list of dicts with keys: pdf_url, title, page_url
    """
    results = []
    seen_urls: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(website_url)

        while True:
            links = await page.evaluate(
                """
                () => Array.from(document.querySelectorAll('a[href$=".pdf"]'))
                    .map(a => ({
                        pdf_url: a.href,
                        title: (a.textContent || a.getAttribute('title') || '').trim(),
                        page_url: window.location.href,
                    }))
            """
            )
            for link in links:
                if link.get("pdf_url") and link["pdf_url"] not in seen_urls:
                    seen_urls.add(link["pdf_url"])
                    results.append(link)

            next_btn = page.locator('a[rel="next"], button[aria-label*="next" i]').first
            if not await next_btn.is_visible() or await next_btn.is_disabled():
                break
            await next_btn.click()
            await page.wait_for_load_state("domcontentloaded")

        await browser.close()
    return results


async def download_pdf_to_bytes(url: str, timeout: float = 60.0) -> bytes | None:
    """
    Downloads a PDF from the given URL and returns its content as bytes.
    Returns None on failure (HTTP error, timeout, non-PDF content).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CDC-WHO-RAG-Bot/1.0; "
            "+https://github.com/SchadenKai/cdc-who-guideline-rag-service)"
        )
    }
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers=headers
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                app_logger.warning("Unexpected content-type %r for %s", content_type, url)
                return None
            return resp.content
    except Exception as e:
        app_logger.error("Failed to download PDF from %s: %s", url, e)
        return None
