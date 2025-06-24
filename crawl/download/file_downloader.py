"""
File Downloader Module - Simplified
Handles downloading of files from URLs.
"""

import asyncio
import boto3
import os
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, Optional
from crawl.detection import _create_http_session


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