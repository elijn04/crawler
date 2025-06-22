"""
File Downloader Module

Handles automatic detection and downloading of files from URLs.
Supports both local storage and AWS S3 upload with smart content-type detection.
"""

import asyncio
import aiohttp
import boto3
import os
import ssl
from urllib.parse import urlparse
from pathlib import Path
from typing import Tuple, Dict, Optional

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "myscapper-downloads")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

# File extensions that should be downloaded instead of scraped
DOWNLOADABLE_EXTENSIONS = {
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    # Videos
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    # Audio
    '.mp3', '.wav', '.flac', '.aac', '.ogg',
    # Data files
    '.txt', '.csv', '.json', '.xml', '.sql'
}

# Content types that indicate downloadable files
DOWNLOADABLE_CONTENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/zip',
    'application/octet-stream',
    'image/',
    'video/',
    'audio/',
    'application/json',
    'text/csv',
    'application/xml'
]

# Browser headers to avoid bot detection
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def is_downloadable_file(url: str) -> bool:
    """
    Check if URL points to a downloadable file based on file extension.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if URL appears to be a downloadable file
        
    Example:
        >>> is_downloadable_file('https://example.com/document.pdf')
        True
        >>> is_downloadable_file('https://example.com/webpage.html')
        False
    """
    parsed_url = urlparse(url)
    file_path = parsed_url.path.lower()
    
    return any(file_path.endswith(extension) for extension in DOWNLOADABLE_EXTENSIONS)


def _create_ssl_context() -> ssl.SSLContext:
    """
    Create SSL context that bypasses certificate verification.
    
    Returns:
        ssl.SSLContext: Configured SSL context for HTTP requests
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


async def check_content_type(url: str) -> Tuple[bool, str]:
    """
    Check if URL points to a downloadable file based on HTTP Content-Type header.
    
    Args:
        url: The URL to check
        
    Returns:
        Tuple[bool, str]: (is_downloadable, content_type)
        
    Example:
        >>> is_downloadable, content_type = await check_content_type('https://example.com/file.pdf')
        >>> print(f"Downloadable: {is_downloadable}, Type: {content_type}")
        Downloadable: True, Type: application/pdf
    """
    try:
        ssl_context = _create_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector, headers=BROWSER_HEADERS) as session:
            async with session.head(url, allow_redirects=True) as response:
                content_type = response.headers.get('content-type', '').lower()
                
                # Check if content type indicates a downloadable file
                is_downloadable = any(
                    download_type in content_type 
                    for download_type in DOWNLOADABLE_CONTENT_TYPES
                )
                
                return is_downloadable, content_type
                
    except Exception as error:
        print(f"Warning: Could not check content type for {url}: {error}")
        return False, ""


async def _download_file_content(url: str) -> Tuple[bytes, str]:
    """
    Download file content from URL.
    
    Args:
        url: The URL to download from
        
    Returns:
        Tuple[bytes, str]: (file_content, content_type)
        
    Raises:
        RuntimeError: If download fails
    """
    ssl_context = _create_ssl_context()
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector, headers=BROWSER_HEADERS) as session:
        async with session.get(url) as response:
            if response.status not in [200, 202]:
                raise RuntimeError(f"Failed to download file: HTTP {response.status}")
            
            file_content = await response.read()
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            return file_content, content_type


def _generate_filename(url: str) -> str:
    """
    Generate filename from URL.
    
    Args:
        url: The source URL
        
    Returns:
        str: Generated filename
    """
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).name
    return filename if filename else "downloaded_file"


async def download_file_locally(url: str, download_dir: str = "downloads") -> Dict:
    """
    Download file from URL and save to local directory.
    
    Args:
        url: The URL to download from
        download_dir: Local directory to save file (default: "downloads")
        
    Returns:
        Dict: Download result with success status and file info
        
    Example:
        >>> result = await download_file_locally('https://example.com/file.pdf')
        >>> if result['success']:
        ...     print(f"File saved to: {result['local_path']}")
    """
    try:
        # Ensure download directory exists
        os.makedirs(download_dir, exist_ok=True)
        
        # Generate local file path
        filename = _generate_filename(url)
        local_file_path = os.path.join(download_dir, filename)
        
        # Download file content
        file_content, content_type = await _download_file_content(url)
        
        # Save file locally
        with open(local_file_path, 'wb') as file:
            file.write(file_content)
        
        return {
            'success': True,
            'file_type': 'download',
            'original_url': url,
            'local_path': local_file_path,
            'file_size': len(file_content),
            'content_type': content_type
        }
        
    except Exception as error:
        return {
            'success': False,
            'file_type': 'download',
            'original_url': url,
            'error': str(error)
        }


async def download_file_to_s3(url: str, s3_key: Optional[str] = None) -> Dict:
    """
    Download file from URL and upload to AWS S3.
    
    Args:
        url: The URL to download from
        s3_key: S3 object key (optional, auto-generated if not provided)
        
    Returns:
        Dict: Download result with success status and S3 info
        
    Example:
        >>> result = await download_file_to_s3('https://example.com/file.pdf')
        >>> if result['success']:
        ...     print(f"File uploaded to: {result['s3_url']}")
    """
    try:
        # Generate S3 key if not provided
        if not s3_key:
            filename = _generate_filename(url)
            s3_key = f"downloads/{filename}"
        
        # Download file content
        file_content, content_type = await _download_file_content(url)
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=S3_REGION)
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        
        return {
            'success': True,
            'file_type': 'download',
            'original_url': url,
            's3_key': s3_key,
            's3_url': s3_url,
            'file_size': len(file_content),
            'content_type': content_type
        }
        
    except Exception as error:
        return {
            'success': False,
            'file_type': 'download',
            'original_url': url,
            'error': str(error)
        }


def _should_use_s3() -> bool:
    """
    Check if S3 should be used based on environment variables.
    
    Returns:
        bool: True if AWS credentials are available
    """
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    return bool(aws_access_key and aws_secret_key)


async def process_file_download(url: str, use_s3: Optional[bool] = None) -> Dict:
    """
    Main function to process a downloadable file URL.
    Automatically chooses between S3 upload and local storage.
    
    Args:
        url: The file URL to download
        use_s3: Force S3 usage (optional, auto-detected if None)
        
    Returns:
        Dict: Download result with success status and file location
        
    Example:
        >>> result = await process_file_download('https://example.com/document.pdf')
        >>> if result['success']:
        ...     print(f"Downloaded successfully!")
        ...     if 's3_url' in result:
        ...         print(f"S3 URL: {result['s3_url']}")
        ...     else:
        ...         print(f"Local path: {result['local_path']}")
    """
    print(f"📁 Downloading file: {url}")
    
    # Auto-detect S3 usage if not specified
    if use_s3 is None:
        use_s3 = _should_use_s3()
    
    if use_s3:
        print("  → Uploading to S3")
        return await download_file_to_s3(url)
    else:
        print("  → Saving locally")
        return await download_file_locally(url)


# Example and testing code
if __name__ == "__main__":
    async def test_download():
        """Test the file download functionality."""
        test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        
        print("Testing file download...")
        result = await process_file_download(test_url)
        
        if result['success']:
            print("✓ Downloaded file successfully:")
            if 's3_url' in result:
                print(f"  S3 URL: {result['s3_url']}")
            else:
                print(f"  Local path: {result['local_path']}")
            print(f"  File size: {result['file_size']} bytes")
            print(f"  Content type: {result['content_type']}")
        else:
            print(f"✗ Download failed: {result['error']}")
    
    # Run the test
    asyncio.run(test_download()) 