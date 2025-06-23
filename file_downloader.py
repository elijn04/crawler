"""
File Downloader Module - Simplified
Handles automatic detection and downloading of files from URLs.
"""

import asyncio
import aiohttp
import boto3
import os
import ssl
from urllib.parse import urlparse
from pathlib import Path
from typing import Tuple, Dict, Optional


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


async def process_file_download(url: str, use_s3: Optional[bool] = None) -> Dict:
    """Download file and save locally or upload to S3."""
    print(f"📁 Downloading file: {url}")
    
    # Auto-detect S3 usage
    if use_s3 is None:
        use_s3 = bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
    
    try:
        # Download file content
        async with _create_http_session() as session:
            async with session.get(url) as response:
                if response.status not in [200, 202]:
                    raise RuntimeError(f"HTTP {response.status}")
                
                file_content = await response.read()
                content_type = response.headers.get('content-type', 'application/octet-stream')
        
        # Generate filename
        filename = Path(urlparse(url).path).name or "downloaded_file"
        
        if use_s3:
            # Upload to S3
            print("  → Uploading to S3")
            s3_key = f"downloads/{filename}"
            bucket_name = os.getenv('S3_BUCKET_NAME', 'myscapper-downloads')
            region = os.getenv('S3_REGION', 'us-east-1')
            
            s3_client = boto3.client('s3', region_name=region)
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                'file_type': 'download',
                'original_url': url,
                's3_key': s3_key,
                's3_url': s3_url,
                'file_size': len(file_content),
                'content_type': content_type
            }
        else:
            # Save locally
            print("  → Saving locally")
            download_dir = "downloads"
            os.makedirs(download_dir, exist_ok=True)
            local_path = os.path.join(download_dir, filename)
            
            with open(local_path, 'wb') as file:
                file.write(file_content)
            
            return {
                'success': True,
                'file_type': 'download',
                'original_url': url,
                'local_path': local_path,
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



