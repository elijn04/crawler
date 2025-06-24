"""
Configuration settings for the web scraper.
"""

from dataclasses import dataclass

@dataclass
class Config:
    """Configuration settings for the scraper.
    
    Attributes:
        headless: Whether to run browser in headless mode
        session_id: Browser session identifier for maintaining state
        wait_for: CSS selector to wait for before considering page loaded
        page_timeout: Timeout in milliseconds for page operations
        scroll_timeout: Timeout in milliseconds for scroll operations
        scroll_delay: Delay in seconds before returning HTML after scroll
        output_filename: Default filename for saving results
        save_to_file: Whether to automatically save results to file
        show_html_preview: Whether to print HTML content to console
        min_login_indicators: Minimum number of login indicators to trigger detection
    """
    headless: bool = True
    session_id: str = "scrape_session"
    wait_for: str = "css:body"
    page_timeout: int = 60000
    scroll_timeout: int = 30000
    scroll_delay: float = 2.0
    output_filename: str = "scraped_data.json"
    save_to_file: bool = True
    show_html_preview: bool = False
    min_login_indicators: int = 4

# Global config instance
config = Config() 