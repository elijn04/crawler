import asyncio
import aiohttp
import boto3
from urllib.parse import urlparse
from pathlib import Path

# S3 Configuration (set these as environment variables or replace with your values)
S3_BUCKET_NAME = "your-bucket-name"
S3_REGION = "us-east-1"

# File extensions that should be downloaded instead of scraped
DOWNLOADABLE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.mp3', '.wav', '.flac', '.aac', '.ogg',
    '.txt', '.csv', '.json', '.xml', '.sql'
}

def is_downloadable_file(url: str) -> bool:
    """Check if URL points to a downloadable file based on extension."""
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(path.endswith(ext) for ext in DOWNLOADABLE_EXTENSIONS)

async def check_content_type(url: str) -> tuple[bool, str]:
    """Check if URL points to a downloadable file based on Content-Type header."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                content_type = response.headers.get('content-type', '').lower()
                
                # Check for non-HTML content types that should be downloaded
                downloadable_types = [
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
                
                is_downloadable = any(dtype in content_type for dtype in downloadable_types)
                return is_downloadable, content_type
    except Exception as e:
        print(f"Warning: Could not check content type for {url}: {e}")
        return False, ""

async def download_file_to_s3(url: str, s3_key: str = None) -> dict:
    """Download file from URL and upload to S3."""
    try:
        # Generate S3 key if not provided
        if not s3_key:
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name or "downloaded_file"
            s3_key = f"downloads/{filename}"
        
        # Download file
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to download file: HTTP {response.status}")
                
                file_content = await response.read()
                content_type = response.headers.get('content-type', 'application/octet-stream')
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=S3_REGION)
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
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
        
    except Exception as e:
        return {
            'success': False,
            'file_type': 'download',
            'original_url': url,
            'error': str(e)
        }

async def process_file_download(url: str) -> dict:
    """Main function to process a downloadable file URL."""
    print(f"📁 Downloading file: {url}")
    return await download_file_to_s3(url)

# Example usage
if __name__ == "__main__":
    async def test():
        test_url = "https://example.com/document.pdf"
        result = await process_file_download(test_url)
        
        if result['success']:
            print(f"✓ Downloaded file to S3:")
            print(f"  S3 URL: {result['s3_url']}")
            print(f"  File size: {result['file_size']} bytes")
            print(f"  Content type: {result['content_type']}")
        else:
            print(f"✗ Failed: {result['error']}")
    
    asyncio.run(test()) 