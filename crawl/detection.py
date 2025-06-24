"""
Detection utilities for web scraping.
Handles file detection and login screen detection.
"""

import aiohttp
import ssl
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Tuple

@dataclass
class Config:
    """Configuration settings for detection.
    
    Attributes:
        min_login_indicators: Minimum number of login indicators to trigger detection
    """
    min_login_indicators: int = 4

config = Config()

# File extensions for downloadable files
DOWNLOADABLE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.mp3', '.wav', '.flac', '.aac', '.ogg',
    '.txt', '.csv', '.json', '.xml', '.sql'
}

# Content types for downloadable files
DOWNLOADABLE_CONTENT_TYPES = [
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel', 'application/vnd.ms-powerpoint', 'application/zip',
    'application/octet-stream', 'image/', 'video/', 'audio/', 'application/json',
    'text/csv', 'application/xml'
]

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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


def _create_http_session():
    """Create HTTP session with SSL bypass."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    return aiohttp.ClientSession(connector=connector, headers=BROWSER_HEADERS)


def is_downloadable_file(url: str) -> bool:
    """Check if URL points to a downloadable file based on extension."""
    parsed_url = urlparse(url)
    file_path = parsed_url.path.lower()
    return any(file_path.endswith(ext) for ext in DOWNLOADABLE_EXTENSIONS)


async def check_content_type(url: str) -> Tuple[bool, str]:
    """Check if URL is downloadable based on HTTP Content-Type header."""
    try:
        async with _create_http_session() as session:
            async with session.head(url, allow_redirects=True) as response:
                content_type = response.headers.get('content-type', '').lower()
                is_downloadable = any(dt in content_type for dt in DOWNLOADABLE_CONTENT_TYPES)
                return is_downloadable, content_type
    except Exception as error:
        print(f"Warning: Could not check content type for {url}: {error}")
        return False, ""


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
