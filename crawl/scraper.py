"""
Web Scraper Module
Handles core web scraping functionality: navigation, scrolling, and HTML extraction.
"""

import asyncio
import logging
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl.detection import check_for_login_screen
from crawl.config import config
from .types import ScrapeResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)


def make_config(**overrides) -> CrawlerRunConfig:
    """Factory for CrawlerRunConfig with base settings.
    
    Creates a CrawlerRunConfig with default settings from the global config,
    allowing specific overrides for individual crawling operations.
    
    Args:
        **overrides: Keyword arguments to override default config values
        
    Returns:
        CrawlerRunConfig: Configured crawler run configuration
    """
    base = {
        'wait_for': config.wait_for,
        'page_timeout': config.page_timeout,
        'session_id': config.session_id,
    }
    base.update(overrides)
    return CrawlerRunConfig(**base)


async def _crawl_steps(crawler, url: str, steps: List[dict]) -> ScrapeResult:
    """Execute a sequence of web crawling operations on the same page.
    
    Runs multiple crawler operations in order, where each step can modify the page
    state (e.g., scroll, click, wait) and the final step captures the resulting HTML.
    Each step uses the URL from the previous step, allowing for redirects and 
    navigation changes.
    
    Args:
        crawler: AsyncWebCrawler instance to perform the operations
        url: Starting URL for the first crawling step
        steps: List of step configurations, where each dict contains crawler
               parameters like 'js_code', 'delay_before_return_html', etc.
        
    Returns:
        ScrapeResult: Contains the final HTML, URL, and status code after all
                     steps complete. HTML and URL come from the last successful step.
        
    Raises:
        RuntimeError: If any step fails during execution
    """
    final_html = ""
    final_url = url
    status_code = 0
    
    for step in steps:
        result = await crawler.arun(url=final_url, config=make_config(**step))
        if not result.success:
            raise RuntimeError(f"Crawl step failed: {result.error_message}")
        
        final_html = result.html or final_html
        final_url = result.url
        status_code = result.status_code
    
    return ScrapeResult(
        success=True,
        url=final_url,
        status_code=status_code,
        html=final_html
    )


async def scrape_webpage(url: str) -> ScrapeResult:
    """Scrape webpage with browser automation and login detection.
    
    Core scraping workflow:
    1. Navigate to the page
    2. Scroll to bottom to load dynamic content  
    3. Extract final HTML content
    4. Check for login requirements
    
    Args:
        url: The webpage URL to scrape
        
    Returns:
        ScrapeResult: Scraping result with success status and content or error details
    """
    try:
        log.info("Processing as webpage: %s", url)
        
        # Scrape the page with browser automation
        browser_config = BrowserConfig(headless=config.headless)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            steps = [
                {},  # Navigate to page
                {   # Scroll to bottom to load dynamic content
                    'js_code': "window.scrollTo(0, document.body.scrollHeight);",
                    'delay_before_return_html': config.scroll_delay,
                    'page_timeout': config.scroll_timeout
                },
                {}  # Extract final HTML
            ]
            
            result = await _crawl_steps(crawler, url, steps)
            
            log.info("Navigated to: %s (Status: %d)", result.url, result.status_code)
            log.info("Scraped %d chars of HTML", len(result.html))
        
        # Check for login screen
        if check_for_login_screen(result.html):
            return ScrapeResult(
                success=False,
                url=url,
                status_code=0,
                html="",
                error_type='login_required',
                message='Page requires authentication',
                instructions=[
                    'Visit the page manually in your browser',
                    'Log in if required', 
                    'Copy and paste the content you need'
                ]
            )
        
        return result
        
    except Exception as error:
        return ScrapeResult(
            success=False,
            url=url,
            status_code=0,
            html="",
            error=str(error),
            error_type='scraping_failed',
            message='Unable to access page automatically',
            possible_causes=[
                'Login/authentication requirements',
                'Anti-bot protection',
                'Network restrictions',
                'Page loading issues'
            ],
            instructions=[
                'Visit the page manually in your browser',
                'Copy and paste the content you need'
            ]
        ) 