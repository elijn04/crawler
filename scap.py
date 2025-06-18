import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from file_downloader import is_downloadable_file, check_content_type

# Configuration
WEBSITE_URL = "https://news.ycombinator.com"
SESSION_ID = "scrape_session"
HEADLESS_MODE = True
PAGE_TIMEOUT = 60000
SCROLL_TIMEOUT = 30000
SCROLL_DELAY = 2.0
WAIT_FOR_ELEMENT = "css:body"

async def check_if_downloadable(url: str) -> bool:
    """Check if URL points to a downloadable file."""
    # First check by extension
    if is_downloadable_file(url):
        return True
    
    # Then check by content type
    is_downloadable, _ = await check_content_type(url)
    return is_downloadable
def check_for_login_screen(html: str) -> bool:
    """Check if page is blocked by login/authentication screen."""
    login_indicators = [
        "login", "sign in", "sign-in", "signin", "log in", "log-in",
        "authentication", "auth", "password", "username", "email",
        "create account", "register", "registration", "subscribe",
        "paywall", "premium", "subscription", "access denied",
        "please log in", "please sign in", "members only",
        "401 unauthorized", "403 forbidden", "access restricted"
    ]
    
    html_lower = html.lower()
    
    # Check for multiple login indicators (more reliable than single matches)
    matches = sum(1 for indicator in login_indicators if indicator in html_lower)
    
    # If we find multiple login-related terms, likely a login screen
    return matches >= 3

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

async def scrape_webpage(url: str) -> dict:
    """Scrape webpage with login detection and graceful error handling."""
    try:
        print(f"🌐 Processing as webpage: {url}")
        
        # Navigate to page
        crawler, result = await navigate_to_page(url)
        print(f"✓ Navigated to: {result.url} (Status: {result.status_code})")
        
        # Scroll to load all content
        await scroll_to_bottom(crawler, result.url)
        print("✓ Scrolled to bottom")
        
        # Get final HTML
        html = await get_outer_html(crawler, result.url)
        
        # Check if page is blocked by login screen
        if check_for_login_screen(html):
            await crawler.__aexit__(None, None, None)
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
        
        print(f"✓ Got HTML ({len(html)} chars)")
        
        await crawler.__aexit__(None, None, None)
        
        return {
            'success': True,
            'url': result.url,
            'status_code': result.status_code,
            'html': html,
            'html_length': len(html)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error_type': 'scraping_failed',
            'error': str(e),
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

# Example usage
if __name__ == "__main__":
    async def test():
        # Test with different types of URLs
        test_urls = [
            "https://news.ycombinator.com",  # Regular webpage
            "https://example.com/document.pdf",  # PDF file (example)
        ]
        
        for url in test_urls:
            print(f"\n{'='*60}")
            print(f"Processing: {url}")
            print('='*60)
            
            # Check if URL is downloadable
            if await check_if_downloadable(url):
                print(f"📁 Detected downloadable file: {url}")
                from file_downloader import process_file_download
                result = await process_file_download(url)
                
                if result['success']:
                    print(f"✓ Downloaded file to S3:")
                    print(f"  S3 URL: {result['s3_url']}")
                    print(f"  File size: {result['file_size']} bytes")
                    print(f"  Content type: {result['content_type']}")
                else:
                    print(f"✗ Download failed: {result['error']}")
            else:
                # Scrape webpage with login detection
                result = await scrape_webpage(url)
                
                if result['success']:
                    print(f"✓ Scraped webpage: {result['url']}")
                    print(f"  Status: {result['status_code']}")
                    print(f"  HTML length: {result['html_length']} chars")
                    print(f"  First 200 chars: {result['html'][:200]}...")
                else:
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
    
    # Run the test
    asyncio.run(test())
