from pathlib import Path
from typing import cast

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
    JsonCssExtractionStrategy,
)
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument
from playwright.async_api import async_playwright
from playwright.async_api._generated import Locator


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
            print("[DEBUG] Gathering button hrefs")
            buttons_href: list[str | None] | None = await page.get_by_label(
                "Download"
            ).evaluate_all("el => el.map(e => e.getAttribute('href')).filter(h => h)")

            if buttons_href is None or buttons_href == []:
                next_page_btn = page.get_by_label("Go to the next page").first
                print("[DEBUG] Navigating to the next page")
                if (
                    not await next_page_btn.is_visible()
                    and await next_page_btn.is_disabled()
                ):
                    print("[DEBUG] Exiting")
                    break
                await next_page_btn.click()

            pdf_download_url.update(buttons_href)

            next_page_btn = page.get_by_label("Go to the next page").first
            print("[DEBUG] Navigating to the next page")
            if (
                not await next_page_btn.is_visible()
                and await next_page_btn.is_disabled()
            ):
                print("[DEBUG] Exiting")
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


def document_extractor(path: Path) -> DoclingDocument:
    doc_converter = DocumentConverter()
    return doc_converter.convert(path).document


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
