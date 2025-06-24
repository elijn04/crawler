"""
Agent_flow_link_scrapper.py - Simple Integration Wrapper
- Easy-to-use class: AgentFlowLinkScrapper() provides a simple interface
- Processes single URL at a time for optimal performance
- Results summary: Provides processing status
- File saving: Optionally saves result to JSON
- Temporary files: Creates temp file ready to be sent somewhere
"""

import asyncio
import os
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from crawl.orchestrator import process_single_url, save_result_to_file

class AgentFlowLinkScrapper:
    """
    Simple web scrapper class for easy integration.
    Optimized for single URL processing.
    
    Usage:
        scrapper = AgentFlowLinkScrapper()
        file_path = scrapper.get_file('https://example.com')
        # Use the file, it will be cleaned up automatically when you're done
    """
    
    def get_file(self, url: str) -> Optional[str]:
        """
        Get file from URL - super simple interface.
        
        Args:
            url: URL to scrape
            
        Returns:
            Path to file with scraped content (or None if failed)
            
        Example:
            file_path = scrapper.get_file('https://news.ycombinator.com')
            if file_path:
                # Use your file here
                with open(file_path, 'r') as f:
                    content = f.read()
        """
        result, temp_file_path = asyncio.run(process_single_url(url))
        
        # Return file path if successful, None if failed  
        if result['status'] in ['success', 'download_success'] and temp_file_path:
            return temp_file_path
        return None
    
    def process_url(self, url: str, save_file: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
        """
        Process a single URL.
        
        Args:
            url: Single URL string to process
            save_file: Optional filename to save result (default: auto-generated)
            
        Returns:
            Tuple containing:
            - Dictionary with processing result
            - Path to temporary file ready to be sent somewhere (or None if failed)
            
        Example:
            result, temp_file = scrapper.process_url('https://news.ycombinator.com')
            
            if temp_file:
                send_file_somewhere(temp_file)
                scrapper.cleanup_temp_file(temp_file)
        """
        # Run async processing through orchestrator
        result, temp_file_path = asyncio.run(process_single_url(url))
        
        # Save to file if requested
        if save_file:
            save_result_to_file(url, result, save_file)
        
        return result, temp_file_path


# Example usage
if __name__ == "__main__":
    print("🚀 AgentFlow Link Scrapper - Simple File Retrieval")
    
    # Example URL
    test_url = "https://httpbin.org/html"
    
    # Get file directly - super simple!
    scrapper = AgentFlowLinkScrapper()
    file_path = scrapper.get_file(test_url)
    
    if file_path:
        print(f"✅ Got file: {file_path}")
        
        # Use the file
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"📄 File size: {len(content)} characters")
    else:
        print("❌ Failed to get file")

 