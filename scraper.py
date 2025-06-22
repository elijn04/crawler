"""
Web Scraper Module

Handles intelligent web scraping with automatic file detection, login detection,
and proper browser session management using Crawl4AI.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from file_downloader import is_downloadable_file, check_content_type

# Browser Configuration
HEADLESS_MODE = True
SESSION_ID = "scrape_session"
WAIT_FOR_ELEMENT = "css:body"
PAGE_TIMEOUT = 60000  # 60 seconds
SCROLL_TIMEOUT = 30000  # 30 seconds
SCROLL_DELAY = 2.0  # 2 seconds

# Output Configuration
OUTPUT_FILENAME = "scraped_data.json"
SAVE_TO_FILE = True
SHOW_HTML_PREVIEW = False

# Login Detection Configuration
STRONG_LOGIN_INDICATORS = [
    "please log in", "please sign in", "login required", "sign in required",
    "authentication required", "access denied", "members only",
    "401 unauthorized", "403 forbidden", "access restricted",
    "subscription required", "premium content", "paywall"
]

LOGIN_FORM_INDICATORS = [
    "password", "username", "login", "sign in", "log in"
]

MIN_LOGIN_INDICATORS = 4


async def check_if_downloadable(url: str) -> bool:
    """
    Determine if URL points to a downloadable file.
    
    Checks both file extension and HTTP Content-Type header to make
    an intelligent decision about whether to download or scrape.
    
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
    # First check by file extension (fast)
    if is_downloadable_file(url):
        return True
    
    # Then check by HTTP Content-Type header (slower but accurate)
    is_downloadable, _ = await check_content_type(url)
    return is_downloadable


def check_for_login_screen(html_content: str) -> bool:
    """
    Detect if webpage is blocked by login/authentication screen.
    
    Uses multiple indicators to determine if the page requires authentication:
    - Strong indicators (any one triggers detection)
    - Form indicators (multiple needed for detection)
    
    Args:
        html_content: The HTML content to analyze
        
    Returns:
        bool: True if login is likely required, False otherwise
        
    Example:
        >>> html = '<html><body>Please log in to continue</body></html>'
        >>> check_for_login_screen(html)
        True
    """
    html_lower = html_content.lower()
    
    # Check for strong login indicators (any one is enough)
    for indicator in STRONG_LOGIN_INDICATORS:
        if indicator in html_lower:
            return True
    
    # Check for login form indicators (need multiple for confidence)
    form_indicator_count = sum(
        1 for indicator in LOGIN_FORM_INDICATORS 
        if indicator in html_lower
    )
    
    # Only trigger if we have strong evidence of a login form
    return form_indicator_count >= MIN_LOGIN_INDICATORS


async def scrape_single_page(url: str, session_id: str = SESSION_ID) -> Dict[str, Any]:
    """
    Scrape a single webpage with proper browser session management.
    
    Performs a complete scraping workflow:
    1. Navigate to the page
    2. Scroll to load dynamic content
    3. Extract final HTML content
    
    Args:
        url: The webpage URL to scrape
        session_id: Browser session identifier for maintaining state
        
    Returns:
        Dict containing scraping results with keys:
            - success: bool indicating if scraping succeeded
            - url: final URL after redirects
            - status_code: HTTP status code
            - html: complete HTML content
            - html_length: length of HTML content
            
    Raises:
        RuntimeError: If navigation fails
        
    Example:
        >>> result = await scrape_single_page('https://example.com')
        >>> if result['success']:
        ...     print(f"Got {result['html_length']} chars of HTML")
    """
    browser_config = BrowserConfig(headless=HEADLESS_MODE)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Step 1: Navigate to the page
        navigation_config = CrawlerRunConfig(
            wait_for=WAIT_FOR_ELEMENT,
            page_timeout=PAGE_TIMEOUT,
            session_id=session_id
        )
        
        navigation_result = await crawler.arun(url=url, config=navigation_config)
        
        if not navigation_result.success:
            raise RuntimeError(f"Navigation failed: {navigation_result.error_message}")
        
        print(f"✓ Navigated to: {navigation_result.url} (Status: {navigation_result.status_code})")
        
        # Step 2: Scroll to load dynamic content
        scroll_config = CrawlerRunConfig(
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            session_id=session_id,
            delay_before_return_html=SCROLL_DELAY,
            page_timeout=SCROLL_TIMEOUT
        )
        
        scroll_result = await crawler.arun(url=navigation_result.url, config=scroll_config)
        if scroll_result.success:
            print("✓ Scrolled to bottom")
        
        # Step 3: Get final HTML content
        final_config = CrawlerRunConfig(session_id=session_id)
        final_result = await crawler.arun(url=navigation_result.url, config=final_config)
        
        return {
            'success': True,
            'url': final_result.url,
            'status_code': final_result.status_code,
            'html': final_result.html,
            'html_length': len(final_result.html)
        }


async def scrape_webpage(url: str) -> Dict[str, Any]:
    """
    Scrape a webpage with login detection and comprehensive error handling.
    
    Attempts to scrape the webpage and detects common issues like:
    - Login/authentication requirements
    - Anti-bot protection
    - Network issues
    
    Args:
        url: The webpage URL to scrape
        
    Returns:
        Dict containing either:
            Success case:
                - success: True
                - url: final URL after redirects
                - status_code: HTTP status code
                - html: complete HTML content
                - html_length: length of HTML content
            
            Failure case:
                - success: False
                - error_type: type of error encountered
                - message: human-readable error message
                - instructions: list of suggested actions
                
    Example:
        >>> result = await scrape_webpage('https://example.com')
        >>> if result['success']:
        ...     html_content = result['html']
        ... else:
        ...     print(f"Error: {result['message']}")
    """
    try:
        print(f"🌐 Processing as webpage: {url}")
        
        # Attempt to scrape the page
        scraping_result = await scrape_single_page(url)
        
        # Check if page is blocked by login screen
        if check_for_login_screen(scraping_result['html']):
            return {
                'success': False,
                'error_type': 'login_required',
                'message': 'Page requires authentication',
                'instructions': [
                    'Visit the page manually in your browser',
                    'Log in if required', 
                    'Copy and paste the content you need'
                ]
            }
        
        print(f"✓ Got HTML ({scraping_result['html_length']} chars)")
        return scraping_result
        
    except Exception as error:
        return {
            'success': False,
            'error_type': 'scraping_failed',
            'error': str(error),
            'message': 'Unable to access page automatically',
            'possible_causes': [
                'Login/authentication requirements',
                'Anti-bot protection',
                'Network restrictions',
                'Page loading issues'
            ],
            'instructions': [
                'Visit the page manually in your browser',
                'Copy and paste the content you need'
            ]
        }


def _print_download_result(result: Dict[str, Any]) -> None:
    """
    Print formatted download result information.
    
    Args:
        result: Download result dictionary from file_downloader
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


def _print_scraping_result(result: Dict[str, Any]) -> None:
    """
    Print formatted webpage scraping result information.
    
    Args:
        result: Scraping result dictionary
    """
    if result['success']:
        print(f"✓ Scraped webpage: {result['url']}")
        print(f"  Status: {result['status_code']}")
        print(f"  HTML length: {result['html_length']} chars")
        print(f"  HTML content captured ✓")
        
        if SHOW_HTML_PREVIEW:
            print("\n--- HTML CONTENT ---")
            print(result['html'])
            print("--- END HTML ---\n")
    else:
        _print_error_details(result)


def _print_error_details(result: Dict[str, Any]) -> None:
    """
    Print detailed error information for failed scraping attempts.
    
    Args:
        result: Failed scraping result dictionary
    """
    if result['error_type'] == 'login_required':
        print("🚫 Login/Authentication Required!")
        print("=" * 60)
        print(f"Sorry, {result['message']}.")
        print("Please:")
        for i, instruction in enumerate(result['instructions'], 1):
            print(f"  {i}. {instruction}")
        print("=" * 60)
    else:
        print(f"✗ Scraping failed: {result['error']}")
        print("=" * 60)
        print(f"{result['message']}.")
        print("This could be due to:")
        for cause in result['possible_causes']:
            print(f"  • {cause}")
        print("")
        print("Please try:")
        for i, instruction in enumerate(result['instructions'], 1):
            print(f"  {i}. {instruction}")
        print("=" * 60)


async def scrape_multiple_websites(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Scrape multiple URLs with intelligent routing to download or scrape.
    
    For each URL, automatically determines whether to:
    - Download as a file (PDFs, images, documents, etc.)
    - Scrape as a webpage (HTML content)
    
    Args:
        urls: List of URLs to process
        
    Returns:
        Dict mapping each URL to its processing result:
            For successful webpage scraping:
                - status: 'success'
                - type: 'webpage'
                - url: final URL after redirects
                - status_code: HTTP status code
                - html_content: complete HTML content
                - html_length: length of HTML content
                
            For successful file downloads:
                - status: 'download_success'
                - type: 'file_download'
                - result: detailed download information
                
            For failures:
                - status: 'failed' or 'download_failed'
                - type: 'webpage' or 'file_download'
                - error_type: type of error
                - error: error message
                
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
        
        # Determine if URL should be downloaded or scraped
        if await check_if_downloadable(url):
            print(f"📁 Detected downloadable file: {url}")
            
            # Import here to avoid circular imports
            from file_downloader import process_file_download
            download_result = await process_file_download(url)
            
            _print_download_result(download_result)
            
            # Store download result
            scraped_results[url] = {
                'status': 'download_success' if download_result['success'] else 'download_failed',
                'type': 'file_download',
                'result': download_result
            }
        else:
            # Process as webpage
            scraping_result = await scrape_webpage(url)
            
            _print_scraping_result(scraping_result)
            
            if scraping_result['success']:
                # Store successful webpage scraping result
                scraped_results[url] = {
                    'status': 'success',
                    'type': 'webpage',
                    'url': scraping_result['url'],
                    'status_code': scraping_result['status_code'],
                    'html_content': scraping_result['html'],
                    'html_length': scraping_result['html_length']
                }
            else:
                # Store failed scraping result
                scraped_results[url] = {
                    'status': 'failed',
                    'type': 'webpage',
                    'error_type': scraping_result['error_type'],
                    'error': scraping_result.get('error', scraping_result.get('message', 'Unknown error'))
                }
    
    return scraped_results


def save_results_to_file(scraped_results: Dict[str, Dict[str, Any]], 
                        filename: Optional[str] = None) -> Optional[str]:
    """
    Save scraping results to JSON file for integration with other programs.
    
    Creates a JSON file containing all scraping results with timestamps
    and complete HTML content for easy integration.
    
    Args:
        scraped_results: Dictionary of scraping results from scrape_multiple_websites
        filename: Output filename (optional, uses default if not provided)
        
    Returns:
        str: Path to saved file, or None if saving is disabled
        
    Example:
        >>> results = await scrape_multiple_websites(['https://example.com'])
        >>> saved_file = save_results_to_file(results, 'my_results.json')
        >>> print(f"Results saved to: {saved_file}")
    """
    if not SAVE_TO_FILE:
        return None
        
    output_filename = filename or OUTPUT_FILENAME
    
    # Prepare data for JSON serialization
    json_data = {}
    current_timestamp = str(time.time())
    
    for url, result_data in scraped_results.items():
        json_data[url] = {
            'status': result_data['status'],
            'type': result_data['type'],
            'timestamp': current_timestamp
        }
        
        # Add specific data based on result type
        if result_data['status'] == 'success':
            json_data[url].update({
                'final_url': result_data['url'],
                'status_code': result_data['status_code'],
                'html_length': result_data['html_length'],
                'html_content': result_data['html_content']  # Full HTML content
            })
        elif 'error' in result_data:
            json_data[url].update({
                'error_type': result_data['error_type'],
                'error': result_data['error']
            })
    
    # Write JSON file with proper encoding
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_filename}")
    return output_filename 