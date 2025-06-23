"""
Web Scraper Module
Handles intelligent web scraping with automatic file detection and login detection.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from file_downloader import is_downloadable_file, check_content_type

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration settings for the scraper.
    
    Attributes:
        headless: Whether to run browser in headless mode
        session_id: Browser session identifier for maintaining state
        wait_for: CSS selector to wait for before considering page loaded
        page_timeout: Timeout in milliseconds for page operations
        scroll_timeout: Timeout in milliseconds for scroll operations
        scroll_delay: Delay in seconds before returning HTML after scroll
        output_filename: Default filename for saving results
        save_to_file: Whether to automatically save results to file
        show_html_preview: Whether to print HTML content to console
        min_login_indicators: Minimum number of login indicators to trigger detection
    """
    headless: bool = True
    session_id: str = "scrape_session"
    wait_for: str = "css:body"
    page_timeout: int = 60000
    scroll_timeout: int = 30000
    scroll_delay: float = 2.0
    output_filename: str = "scraped_data.json"
    save_to_file: bool = True
    show_html_preview: bool = False
    min_login_indicators: int = 4

@dataclass
class ScrapeResult:
    """Result of a scraping operation.
    
    Attributes:
        success: Whether the scraping operation succeeded
        url: Final URL after redirects
        status_code: HTTP status code
        html: Complete HTML content
        error: Error message if operation failed
        error_type: Type of error (e.g., 'login_required', 'scraping_failed')
        message: Human-readable error message
        instructions: List of suggested actions for user
        possible_causes: List of possible causes for failure
        
    Properties:
        html_length: Length of HTML content in characters
    """
    success: bool
    url: str
    status_code: int
    html: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    instructions: Optional[List[str]] = None
    possible_causes: Optional[List[str]] = None
    
    @property
    def html_length(self) -> int:
        """Get the length of HTML content in characters.
        
        Returns:
            int: Number of characters in HTML content
        """
        return len(self.html)

config = Config()

# Login Detection
STRONG_LOGIN_INDICATORS = [
    "please log in", "please sign in", "login required", "sign in required",
    "authentication required", "access denied", "members only",
    "401 unauthorized", "403 forbidden", "access restricted",
    "subscription required", "premium content", "paywall"
]

LOGIN_FORM_INDICATORS = [
    "password", "username", "login", "sign in", "log in"
]


def make_config(**overrides) -> CrawlerRunConfig:
    """Factory for CrawlerRunConfig with base settings.
    
    Creates a CrawlerRunConfig with default settings from the global config,
    allowing specific overrides for individual crawling operations.
    
    Args:
        **overrides: Keyword arguments to override default config values
        
    Returns:
        CrawlerRunConfig: Configured crawler run configuration
        
    Example:
        >>> config = make_config(js_code="window.scrollTo(0, 0);")
        >>> # Creates config with default settings plus custom JS code
    """
    base = {
        'wait_for': config.wait_for,
        'page_timeout': config.page_timeout,
        'session_id': config.session_id,
    }
    base.update(overrides)
    return CrawlerRunConfig(**base)


async def check_if_downloadable(url: str) -> bool:
    """Check if URL should be downloaded or scraped.
    
    Determines whether a URL points to a downloadable file by checking
    both the file extension and HTTP Content-Type header.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if URL should be downloaded, False if it should be scraped
        
    Example:
        >>> await check_if_downloadable('https://example.com/document.pdf')
        True
        >>> await check_if_downloadable('https://example.com/webpage.html')
        False
    """
    if is_downloadable_file(url):
        return True
    is_downloadable, _ = await check_content_type(url)
    return is_downloadable


def check_for_login_screen(html: str) -> bool:
    """Detect if webpage requires authentication.
    
    Analyzes HTML content to determine if the page is blocked by a login
    or authentication screen using multiple indicators.
    
    Args:
        html: The HTML content to analyze
        
    Returns:
        bool: True if login is likely required, False otherwise
        
    Example:
        >>> html = '<html><body>Please log in to continue</body></html>'
        >>> check_for_login_screen(html)
        True
        >>> html = '<html><body>Welcome to our site!</body></html>'
        >>> check_for_login_screen(html)
        False
    """
    low = html.lower()
    if any(ind in low for ind in STRONG_LOGIN_INDICATORS):
        return True
    return sum(ind in low for ind in LOGIN_FORM_INDICATORS) >= config.min_login_indicators


async def _crawl_steps(crawler, url: str, steps: List[dict]) -> ScrapeResult:
    """Execute a series of crawling steps.
    
    Performs multiple crawler operations in sequence, typically used for
    navigation, scrolling, and final content extraction.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: Starting URL for crawling
        steps: List of dictionaries containing step configurations
        
    Returns:
        ScrapeResult: Result of the final crawling step
        
    Raises:
        RuntimeError: If any crawling step fails
        
    Example:
        >>> steps = [
        ...     {},  # Navigate
        ...     {'js_code': 'window.scrollTo(0, document.body.scrollHeight);'},  # Scroll
        ...     {}   # Final HTML
        ... ]
        >>> result = await _crawl_steps(crawler, url, steps)
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
    """Scrape webpage with browser automation, login detection and error handling.
    
    Performs a complete scraping workflow including:
    1. Navigation to the page
    2. Scrolling to load dynamic content  
    3. Final HTML content extraction
    4. Login detection and error handling
    
    Args:
        url: The webpage URL to scrape
        
    Returns:
        ScrapeResult: Scraping result with success status and content or error details
        
    Example:
        >>> result = await scrape_webpage('https://example.com')
        >>> if result.success:
        ...     html_content = result.html
        ... else:
        ...     print(f"Error: {result.message}")
    """
    try:
        log.info("Processing as webpage: %s", url)
        
        # Scrape the page with browser automation
        browser_config = BrowserConfig(headless=config.headless)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            steps = [
                {},  # Navigate
                {   # Scroll
                    'js_code': "window.scrollTo(0, document.body.scrollHeight);",
                    'delay_before_return_html': config.scroll_delay,
                    'page_timeout': config.scroll_timeout
                },
                {}  # Final HTML
            ]
            
            result = await _crawl_steps(crawler, url, steps)
            
            log.info("Navigated to: %s (Status: %d)", result.url, result.status_code)
            log.info("Scraped %d chars of HTML", result.html_length)
        
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


def _print_download(result: Dict[str, Any]) -> None:
    """Print download result information.
    
    Formats and prints the result of a file download operation,
    including success status, file location, and error details.
    
    Args:
        result: Download result dictionary from file_downloader module
        
    Example:
        >>> download_result = {'success': True, 'local_path': '/downloads/file.pdf'}
        >>> _print_download(download_result)
        ✓ Downloaded file successfully:
          Local path: /downloads/file.pdf
    """
    if result['success']:
        print("✓ Downloaded file successfully:")
        if 's3_url' in result:
            print(f"  S3 URL: {result['s3_url']}")
        if 'local_path' in result:
            print(f"  Local path: {result['local_path']}")
        print(f"  File size: {result['file_size']} bytes")
        print(f"  Content type: {result['content_type']}")
    else:
        print(f"✗ Download failed: {result['error']}")


def _print_webpage(result: ScrapeResult) -> None:
    """Print webpage scraping result information.
    
    Formats and prints the result of a webpage scraping operation,
    including success status, HTML content info, and detailed error messages.
    
    Args:
        result: ScrapeResult instance containing scraping results
        
    Example:
        >>> scrape_result = ScrapeResult(success=True, url='https://example.com', ...)
        >>> _print_webpage(scrape_result)
        ✓ Scraped webpage: https://example.com
          Status: 200
          HTML length: 1234 chars
    """
    if result.success:
        print(f"✓ Scraped webpage: {result.url}")
        print(f"  Status: {result.status_code}")
        print(f"  HTML length: {result.html_length} chars")
        print(f"  HTML content captured ✓")
        
        if config.show_html_preview:
            print("\n--- HTML CONTENT ---")
            print(result.html)
            print("--- END HTML ---\n")
    else:
        if result.error_type == 'login_required':
            print("🚫 Login/Authentication Required!")
            print("=" * 60)
            print(f"Sorry, {result.message}.")
            print("Please:")
            for i, instruction in enumerate(result.instructions, 1):
                print(f"  {i}. {instruction}")
            print("=" * 60)
        else:
            print(f"✗ Scraping failed: {result.error}")
            print("=" * 60)
            print(f"{result.message}.")
            if result.possible_causes:
                print("This could be due to:")
                for cause in result.possible_causes:
                    print(f"  • {cause}")
            print("\nPlease try:")
            for i, instruction in enumerate(result.instructions, 1):
                print(f"  {i}. {instruction}")
            print("=" * 60)


async def scrape_multiple_websites(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    """Scrape multiple URLs with intelligent routing.
    
    Processes a list of URLs, automatically determining whether each should
    be downloaded as a file or scraped as a webpage. Provides comprehensive
    results for each URL.
    
    Args:
        urls: List of URLs to process
        
    Returns:
        Dict mapping each URL to its processing result containing:
            - status: 'success', 'download_success', 'failed', or 'download_failed'
            - type: 'webpage' or 'file_download'
            - Additional fields depending on success/failure and type
        
    Example:
        >>> urls = ['https://example.com', 'https://example.com/file.pdf']
        >>> results = await scrape_multiple_websites(urls)
        >>> for url, result in results.items():
        ...     print(f"{url}: {result['status']}")
    """
    scraped_results = {}
    
    for url in urls:
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print('='*60)
        
        # Check if downloadable
        if await check_if_downloadable(url):
            print(f"📁 Detected downloadable file: {url}")
            
            from file_downloader import process_file_download
            download_result = await process_file_download(url)
            
            _print_download(download_result)
            
            scraped_results[url] = {
                'status': 'download_success' if download_result['success'] else 'download_failed',
                'type': 'file_download',
                'result': download_result
            }
        else:
            # Process as webpage
            scraping_result = await scrape_webpage(url)
            
            _print_webpage(scraping_result)
            
            if scraping_result.success:
                scraped_results[url] = {
                    'status': 'success',
                    'type': 'webpage',
                    'url': scraping_result.url,
                    'status_code': scraping_result.status_code,
                    'html_content': scraping_result.html,
                    'html_length': scraping_result.html_length
                }
            else:
                scraped_results[url] = {
                    'status': 'failed',
                    'type': 'webpage',
                    'error_type': scraping_result.error_type,
                    'error': scraping_result.error or scraping_result.message or 'Unknown error'
                }
    
    return scraped_results


def save_results_to_file(scraped_results: Dict[str, Dict[str, Any]], 
                        filename: Optional[str] = None) -> Optional[str]:
    """Save scraping results to JSON file.
    
    Serializes scraping results to a JSON file with timestamps and complete
    content for easy integration with other programs.
    
    Args:
        scraped_results: Dictionary of scraping results from scrape_multiple_websites
        filename: Output filename (optional, uses default if not provided)
        
    Returns:
        Optional[str]: Path to saved file, or None if saving is disabled
        
    Example:
        >>> results = await scrape_multiple_websites(['https://example.com'])
        >>> saved_file = save_results_to_file(results, 'my_results.json')
        >>> print(f"Results saved to: {saved_file}")
    """
    if not config.save_to_file:
        return None
        
    output_filename = filename or config.output_filename
    json_data = {}
    current_timestamp = str(time.time())
    
    for url, result_data in scraped_results.items():
        json_data[url] = {
            'status': result_data['status'],
            'type': result_data['type'],
            'timestamp': current_timestamp
        }
        
        if result_data['status'] == 'success':
            json_data[url].update({
                'final_url': result_data['url'],
                'status_code': result_data['status_code'],
                'html_length': result_data['html_length'],
                'html_content': result_data['html_content']
            })
        elif 'error' in result_data:
            json_data[url].update({
                'error_type': result_data['error_type'],
                'error': result_data['error']
            })
    
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_filename}")
    return output_filename 