from typing import Dict, Any
from .types import ScrapeResult
from .config import config


def print_processing_result(url: str, result: Dict[str, Any]) -> None:
    """Print the result of processing a URL (either file download or webpage scraping).
    
    Args:
        url: The URL that was processed
        result: Processing result containing status, type, and details
    """
    print(f"\n{'='*60}")
    print(f"Processing: {url}")
    print('='*60)
    
    if result['type'] == 'file_download':
        print(f"📁 Detected downloadable file: {url}")
        _print_download(result['result'])
    else:  # webpage
        _print_webpage(result['scraping_result'])


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
        print(f"  HTML length: {len(result.html)} chars")
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
