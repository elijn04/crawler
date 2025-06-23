
"""
Agent_flow_link_scrapper.py - Simple Integration Wrapper
- Easy-to-use class: AgentFlowLinkScrapper() provides a simple interface
- Flexible input: Accepts single URL or list of URLs
- Results summary: Provides statistics on success/failure rates
- File saving: Optionally saves results to JSON
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
            
            # For single URL
            results = scrapper.process_urls('https://example.com')
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


# Example usage
if __name__ == "__main__":
    # Example 1: Simple usage
    print("🚀 AgentFlow Link Scrapper Example Usage")
    
    
    # Example URLs
    test_urls = [
        "https://monkeyandmekitchenadventures.com/asian-cabbage-noodle-stir-fry/",
        "https://www.groovelife.com/?srsltid=AfmBOoroLYtL2YJOHUZzwkh160M9edmAXxxDPsTmmgnetZU3pfYiijiG",
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
    
    # Alternative: Direct usage
    # scrapper = AgentFlowLinkScrapper()
    # results = scrapper.process_urls("https://example.com")  # Single URL
    # results = scrapper.process_urls(["https://site1.com", "https://site2.com"])  # Multiple URLs
    
    print("\n✅ Example complete!") 