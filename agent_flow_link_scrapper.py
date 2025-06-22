#!/usr/bin/env python3
"""
AgentFlow Link Scrapper - Simple Integration Module

Easy-to-use web scraping and file downloading for integration into existing systems.
"""

import asyncio
import os
from typing import List, Dict, Union, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from scraper import scrape_multiple_websites, save_results_to_file

class AgentFlowLinkScrapper:
    """
    Simple web scrapper class for easy integration.
    
    Usage:
        scrapper = AgentFlowLinkScrapper()
        results = scrapper.process_urls(['https://example.com', 'https://file.pdf'])
    """
    
    def __init__(self, 
                 aws_access_key: Optional[str] = None,
                 aws_secret_key: Optional[str] = None,
                 s3_bucket: Optional[str] = None,
                 s3_region: Optional[str] = None):
        """
        Initialize scrapper with optional AWS credentials.
        
        Args:
            aws_access_key: AWS access key (or set AWS_ACCESS_KEY_ID env var)
            aws_secret_key: AWS secret key (or set AWS_SECRET_ACCESS_KEY env var) 
            s3_bucket: S3 bucket name (or set S3_BUCKET_NAME env var)
            s3_region: S3 region (or set S3_REGION env var)
        """
        # Set AWS credentials if provided
        if aws_access_key:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
        if aws_secret_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
        if s3_bucket:
            os.environ['S3_BUCKET_NAME'] = s3_bucket
        if s3_region:
            os.environ['S3_REGION'] = s3_region
    
    def process_urls(self, urls: Union[str, List[str]], save_file: Optional[str] = None) -> Dict:
        """
        Process single URL or list of URLs.
        
        Args:
            urls: Single URL string or list of URLs
            save_file: Optional filename to save results (default: auto-generated)
            
        Returns:
            Dictionary with results for each URL
            
        Example:
            results = scrapper.process_urls([
                'https://news.ycombinator.com',
                'https://example.com/document.pdf'
            ])
        """
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
        
        # Run async scraping
        results = asyncio.run(scrape_multiple_websites(urls))
        
        # Save to file if requested
        if save_file:
            save_results_to_file(results, save_file)
        
        return results
    
    def process_url(self, url: str, save_file: Optional[str] = None) -> Dict:
        """
        Process a single URL (convenience method).
        
        Args:
            url: URL to process
            save_file: Optional filename to save results
            
        Returns:
            Dictionary with result for the URL
        """
        results = self.process_urls([url], save_file)
        return results[url]
    
    def get_summary(self, results: Dict) -> Dict:
        """
        Get summary statistics from results.
        
        Args:
            results: Results dictionary from process_urls()
            
        Returns:
            Summary statistics
        """
        total = len(results)
        successful = sum(1 for data in results.values() 
                        if data['status'] in ['success', 'download_success'])
        failed = total - successful
        
        # Count by type
        webpages = sum(1 for data in results.values() if data['type'] == 'webpage')
        downloads = sum(1 for data in results.values() if data['type'] == 'file_download')
        
        return {
            'total_processed': total,
            'successful': successful,
            'failed': failed,
            'webpages_scraped': webpages,
            'files_downloaded': downloads,
            'success_rate': round(successful / total * 100, 1) if total > 0 else 0
        }

# Convenience functions for simple usage
def scrape_url(url: str, save_file: Optional[str] = None) -> Dict:
    """
    Simple function to scrape a single URL.
    
    Args:
        url: URL to scrape
        save_file: Optional filename to save results
        
    Returns:
        Result dictionary for the URL
    """
    scrapper = AgentFlowLinkScrapper()
    return scrapper.process_url(url, save_file)

def scrape_urls(urls: List[str], save_file: Optional[str] = None) -> Dict:
    """
    Simple function to scrape multiple URLs.
    
    Args:
        urls: List of URLs to scrape
        save_file: Optional filename to save results
        
    Returns:
        Results dictionary for all URLs
    """
    scrapper = AgentFlowLinkScrapper()
    return scrapper.process_urls(urls, save_file)

def configure_aws(access_key: str, secret_key: str, bucket_name: str, region: str = 'us-east-1'):
    """
    Configure AWS credentials for S3 file uploads.
    
    Args:
        access_key: AWS access key ID
        secret_key: AWS secret access key
        bucket_name: S3 bucket name
        region: AWS region (default: us-east-1)
    """
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    os.environ['S3_BUCKET_NAME'] = bucket_name
    os.environ['S3_REGION'] = region

# Example usage
if __name__ == "__main__":
    # Example 1: Simple usage
    print("🚀 AgentFlow Link Scrapper Example Usage")
    
    # Configure AWS (optional - can also use .env file)
    # configure_aws('your-key', 'your-secret', 'your-bucket')
    
    # Example URLs
    test_urls = [
        "https://news.ycombinator.com",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    ]
    
    # Method 1: Using class
    scrapper = AgentFlowLinkScrapper()
    results = scrapper.process_urls(test_urls, save_file="example_results.json")
    summary = scrapper.get_summary(results)
    
    print(f"\n📊 Summary:")
    print(f"  Total processed: {summary['total_processed']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success rate: {summary['success_rate']}%")
    
    # Method 2: Using convenience functions
    # single_result = scrape_url("https://example.com")
    # bulk_results = scrape_urls(["https://site1.com", "https://site2.com"])
    
    print("\n✅ Example complete!") 