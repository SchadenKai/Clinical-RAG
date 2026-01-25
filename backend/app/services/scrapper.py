from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
    JsonCssExtractionStrategy,
)


async def simple_crawler(url: str) -> CrawlResult:
    browser_config = BrowserConfig()
    # TODO: configure this for CDC / WHO website
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
