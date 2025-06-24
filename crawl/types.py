"""
Types Module
Contains shared data structures used across the crawl package.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ScrapeResult:
    """Result of a scraping operation.
    
    Attributes:
        success: Whether the scraping operation succeeded
        url: Final URL after redirects
        status_code: HTTP status code
        html: Complete HTML content
        error: Error message if operation failed
        error_type: Type of error (e.g., 'login_required', 'scraping_failed')
        message: Human-readable error message
        instructions: List of suggested actions for user
        possible_causes: List of possible causes for failure
        
    Properties:
        html_length: Length of HTML content in characters
    """
    success: bool
    url: str
    status_code: int
    html: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    instructions: Optional[List[str]] = None
    possible_causes: Optional[List[str]] = None 