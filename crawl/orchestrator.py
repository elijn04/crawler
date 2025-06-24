"""
Orchestrator Module
Coordinates the scraping workflow: detection, scraping, downloading, and printing.
Optimized for single URL processing.
"""

import json
import time
import os
from typing import Dict, Any, Optional, Tuple
from .config import config
from .detection import check_if_downloadable
from .scraper import scrape_webpage
from .print import print_processing_result
from .temp_file import TempFileManager


async def process_single_url(url: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Process a single URL and return result with temp file path.
    
    Coordinates the complete workflow:
    1. Checks if URL is downloadable (detection.py)
    2. Routes to appropriate processor (scraper.py or file_downloader)
    3. For webpages: cleans HTML and converts to temporary markdown file (temp_file.py)
    4. For documents: creates temporary copy (temp_file.py)
    5. Handles printing (print.py)
    
    Args:
        url: Single URL to process
        
    Returns:
        Tuple containing:
        - Dict with processing result for the URL
        - Path to temporary file ready to be sent somewhere (or None if failed)
    """
    temp_file_path = None
    
    # Create temp file manager for this URL
    temp_manager = TempFileManager()
    
    # Detection phase
    is_downloadable = await check_if_downloadable(url)
    
    if is_downloadable:
        # File download path
        from crawl.download.file_downloader import process_file_download
        download_result = await process_file_download(url)
        
        if download_result['success']:
            # Create temp copy of downloaded file using temp_file.py
            source_path = download_result.get('local_path')
            if source_path and os.path.exists(source_path):
                original_filename = os.path.basename(source_path)
                temp_file_path = temp_manager.create_temp_document(source_path, original_filename)
        
        result = {
            'status': 'download_success' if download_result['success'] else 'download_failed',
            'type': 'file_download',
            'url': url,
            'temp_file': temp_file_path,
            'result': download_result
        }
    else:
        # Webpage scraping path
        scraping_result = await scrape_webpage(url)
        
        if scraping_result.success:
            # Convert to temporary markdown file using temp_file.py
            temp_file_path = temp_manager.create_temp_markdown(scraping_result.html, scraping_result.url)
            
            result = {
                'status': 'success',
                'type': 'webpage',
                'url': scraping_result.url,
                'status_code': scraping_result.status_code,
                'html_content': scraping_result.html,
                'html_length': len(scraping_result.html),
                'temp_file': temp_file_path,
                'scraping_result': scraping_result
            }
        else:
            result = {
                'status': 'failed',
                'type': 'webpage',
                'url': url,
                'error_type': scraping_result.error_type,
                'error': scraping_result.error or scraping_result.message or 'Unknown error',
                'scraping_result': scraping_result
            }
    
    # Printing phase
    print_processing_result(url, result)
    
    # Summary
    if temp_file_path:
        file_size = os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0
        print(f"\n📄 Created temporary file: {os.path.basename(temp_file_path)} ({file_size} bytes)")
        print(f"📁 Temp directory: {temp_manager.get_temp_dir()}")
        print("🚀 File ready to be sent somewhere!")
    
    return result, temp_file_path


def cleanup_temp_file(temp_file_path: Optional[str]) -> None:
    """Clean up a single temporary file and its directory.
    
    Args:
        temp_file_path: Path to temporary file to clean up
    """
    if not temp_file_path or not os.path.exists(temp_file_path):
        return
    
    # Get the temp directory
    temp_dir = os.path.dirname(temp_file_path)
    
    if temp_dir and os.path.exists(temp_dir):
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🗑️  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️  Error cleaning up temp directory: {e}")


def save_result_to_file(url: str, result_data: Dict[str, Any], 
                       filename: Optional[str] = None) -> Optional[str]:
    """Save single URL result to JSON file.
    
    Args:
        url: The processed URL
        result_data: Processing result for the URL
        filename: Output filename (optional, uses default if not provided)
        
    Returns:
        Optional[str]: Path to saved file, or None if saving is disabled
    """
    if not config.save_to_file:
        return None
        
    output_filename = filename or f"scraped_{int(time.time())}.json"
    current_timestamp = str(time.time())
    
    json_data = {
        url: {
            'status': result_data['status'],
            'type': result_data['type'],
            'timestamp': current_timestamp
        }
    }
    
    if result_data['status'] == 'success':
        json_data[url].update({
            'final_url': result_data['url'],
            'status_code': result_data['status_code'],
            'html_length': result_data['html_length'],
            'temp_file': result_data.get('temp_file')
        })
    elif result_data['status'] == 'download_success':
        json_data[url].update({
            'temp_file': result_data.get('temp_file'),
            'file_info': {
                'size': result_data['result'].get('file_size'),
                'content_type': result_data['result'].get('content_type')
            }
        })
    elif 'error' in result_data:
        json_data[url].update({
            'error_type': result_data['error_type'],
            'error': result_data['error']
        })
    
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Result saved to: {output_filename}")
    return output_filename 