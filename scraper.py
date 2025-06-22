import asyncio
import json
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from file_downloader import is_downloadable_file, check_content_type

# Configuration constants (moved from config.py)
HEADLESS_MODE = True
SESSION_ID = "scrape_session"
WAIT_FOR_ELEMENT = "css:body"
PAGE_TIMEOUT = 60000  # 60 seconds
SCROLL_TIMEOUT = 30000  # 30 seconds
SCROLL_DELAY = 2.0  # 2 seconds
OUTPUT_FILENAME = "scraped_data.json"
SAVE_TO_FILE = True
SHOW_HTML_PREVIEW = False

# Login detection settings
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
    """Check if URL points to a downloadable file."""
    # First check by extension
    if is_downloadable_file(url):
        return True
    
    # Then check by content type
    is_downloadable, _ = await check_content_type(url)
    return is_downloadable

def check_for_login_screen(html: str) -> bool:
    """Check if page is blocked by login/authentication screen."""
    html_lower = html.lower()
    
    # Check for strong indicators (any one suggests login required)
    for indicator in STRONG_LOGIN_INDICATORS:
        if indicator in html_lower:
            return True
    
    # Check for login form indicators (need multiple to suggest login screen)
    form_matches = sum(1 for indicator in LOGIN_FORM_INDICATORS if indicator in html_lower)
    
    # Only trigger if we have strong evidence of a login form
    return form_matches >= MIN_LOGIN_INDICATORS

async def scrape_single_page(url: str, session_id: str = SESSION_ID):
    """Complete scraping workflow for a single page using proper context management."""
    browser_cfg = BrowserConfig(headless=HEADLESS_MODE)
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # Step 1: Navigate to page
        run_cfg = CrawlerRunConfig(
            wait_for=WAIT_FOR_ELEMENT,
            page_timeout=PAGE_TIMEOUT,
            session_id=session_id
        )
        
        result = await crawler.arun(url=url, config=run_cfg)
        
        if not result.success:
            raise RuntimeError(f"Navigation failed: {result.error_message}")
        
        print(f"✓ Navigated to: {result.url} (Status: {result.status_code})")
        
        # Step 2: Scroll to load dynamic content
        scroll_cfg = CrawlerRunConfig(
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            session_id=session_id,
            delay_before_return_html=SCROLL_DELAY,
            page_timeout=SCROLL_TIMEOUT
        )
        
        scroll_result = await crawler.arun(url=result.url, config=scroll_cfg)
        if scroll_result.success:
            print("✓ Scrolled to bottom")
        
        # Step 3: Get final content
        final_result = await crawler.arun(url=result.url, config=CrawlerRunConfig(session_id=session_id))
        
        return {
            'success': True,
            'url': final_result.url,
            'status_code': final_result.status_code,
            'html': final_result.html,
            'html_length': len(final_result.html)
        }

# Helper functions removed - now using proper context management in scrape_single_page

async def scrape_webpage(url: str) -> dict:
    """Scrape webpage with login detection and graceful error handling."""
    try:
        print(f"🌐 Processing as webpage: {url}")
        
        # Use the new proper context management function
        result = await scrape_single_page(url)
        
        # Check if page is blocked by login screen
        if check_for_login_screen(result['html']):
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
        
        print(f"✓ Got HTML ({result['html_length']} chars)")
        
        return result
        
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

async def scrape_multiple_websites(urls: list) -> dict:
    """
    Scrape multiple websites and return organized results.
    Returns: Dictionary with scraped data for each URL
    """
    scraped_results = {}
    
    for url in urls:
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print('='*60)
        
        # Check if URL is downloadable
        if await check_if_downloadable(url):
            print(f"📁 Detected downloadable file: {url}")
            from file_downloader import process_file_download
            result = await process_file_download(url)
            
            if result['success']:
                print(f"✓ Downloaded file successfully:")
                if 's3_url' in result:
                    print(f"  S3 URL: {result['s3_url']}")
                if 'local_path' in result:
                    print(f"  Local path: {result['local_path']}")
                print(f"  File size: {result['file_size']} bytes")
                print(f"  Content type: {result['content_type']}")
            else:
                print(f"✗ Download failed: {result['error']}")
                
            # Store download result
            scraped_results[url] = {
                'status': 'download_success' if result['success'] else 'download_failed',
                'type': 'file_download',
                'result': result
            }
        else:
            # Scrape webpage
            result = await scrape_webpage(url)
            
            if result['success']:
                print(f"✓ Scraped webpage: {result['url']}")
                print(f"  Status: {result['status_code']}")
                print(f"  HTML length: {result['html_length']} chars")
                print(f"  HTML content captured ✓")
                
                if SHOW_HTML_PREVIEW:
                    print(f"\n--- HTML CONTENT ---")
                    print(result['html'])
                    print(f"--- END HTML ---\n")
                
                # Store successful scrape
                scraped_results[url] = {
                    'status': 'success',
                    'type': 'webpage',
                    'url': result['url'],
                    'status_code': result['status_code'],
                    'html_content': result['html'],
                    'html_length': result['html_length']
                }
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
                    
                # Store failed result
                scraped_results[url] = {
                    'status': 'failed',
                    'type': 'webpage',
                    'error_type': result['error_type'],
                    'error': result.get('error', result.get('message', 'Unknown error'))
                }
    
    return scraped_results

def save_results_to_file(scraped_results: dict, filename: str = None):
    """Save results to JSON file for integration with other programs."""
    if not SAVE_TO_FILE:
        return None
        
    filename = filename or OUTPUT_FILENAME
    
    # Prepare data for JSON serialization
    json_data = {}
    for url, data in scraped_results.items():
        json_data[url] = {
            'status': data['status'],
            'type': data['type'],
            'timestamp': str(time.time())
        }
        
        if data['status'] == 'success':
            json_data[url].update({
                'final_url': data['url'],
                'status_code': data['status_code'],
                'html_length': data['html_length'],
                'html_content': data['html_content']  # Full HTML content
            })
        elif 'error' in data:
            json_data[url].update({
                'error_type': data['error_type'],
                'error': data['error']
            })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {filename}")
    return filename 