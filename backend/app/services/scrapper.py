from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
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
