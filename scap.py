import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

# Configuration
WEBSITE_URL = "https://news.ycombinator.com"
SESSION_ID = "scrape_session"
HEADLESS_MODE = True
PAGE_TIMEOUT = 60000
SCROLL_TIMEOUT = 30000
SCROLL_DELAY = 2.0
WAIT_FOR_ELEMENT = "css:body"

async def navigate_to_page(url: str, session_id: str = SESSION_ID):
    """Navigate to a webpage and return crawler + result."""
    browser_cfg = BrowserConfig(browser_mode="playwright", headless=HEADLESS_MODE)
    run_cfg = CrawlerRunConfig(
        wait_for=WAIT_FOR_ELEMENT,
        page_timeout=PAGE_TIMEOUT,
        session_id=session_id
    )
    
    crawler = AsyncWebCrawler(config=browser_cfg)
    await crawler.__aenter__()
    
    result = await crawler.arun(url=url, config=run_cfg)
    
    if not result.success:
        await crawler.__aexit__(None, None, None)
        raise RuntimeError(f"Navigation failed: {result.error_message}")
    
    return crawler, result

async def scroll_to_bottom(crawler, url: str, session_id: str = SESSION_ID):
    """Scroll to bottom to load all dynamic content."""
    scroll_cfg = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        js_only=True,
        session_id=session_id,
        delay_before_return_html=SCROLL_DELAY,
        page_timeout=SCROLL_TIMEOUT
    )
    
    result = await crawler.arun(url=url, config=scroll_cfg)
    
    if not result.success:
        raise RuntimeError(f"Scroll failed: {result.error_message}")
    
    return result

async def get_outer_html(crawler, url: str, session_id: str = SESSION_ID):
    """Get the complete HTML after all content is loaded."""
    html_cfg = CrawlerRunConfig(
        js_only=True,
        session_id=session_id,
        page_timeout=SCROLL_TIMEOUT
    )
    
    result = await crawler.arun(url=url, config=html_cfg)
    
    if not result.success:
        raise RuntimeError(f"HTML retrieval failed: {result.error_message}")
    
    return result.html

# Example usage
if __name__ == "__main__":
    async def test():
        # Navigate to page
        crawler, result = await navigate_to_page(WEBSITE_URL)
        print(f"✓ Navigated to: {result.url} (Status: {result.status_code})")
        
        # Scroll to load all content
        await scroll_to_bottom(crawler, result.url)
        print("✓ Scrolled to bottom")
        
        # Get final HTML
        html = await get_outer_html(crawler, result.url)
        print(f"✓ Got HTML ({len(html)} chars)")
        print("=" * 50)
        print(html)
        
        await crawler.__aexit__(None, None, None)
    
    asyncio.run(test())
