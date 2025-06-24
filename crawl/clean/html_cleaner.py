"""
HTML Cleaner Module
Cleans and processes HTML content using parsing utilities.
"""

import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from crawl.clean.parsing import extract_description


def clean_html(html_content: str) -> str:
    """Clean HTML by removing unwanted elements and extracting text.
    
    Args:
        html_content: Raw HTML content to clean
        
    Returns:
        Cleaned HTML content
    """
    if not html_content:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    unwanted_tags = [
        'script', 'style', 'nav', 'header', 'footer', 
        'aside', 'iframe', 'noscript', 'meta', 'link'
    ]
    
    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()
    
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()
    
    # Remove empty elements
    for element in soup.find_all():
        if not element.get_text(strip=True) and not element.find_all(['img', 'br', 'hr']):
            element.decompose()
    
    return str(soup)


def extract_text_content(html: str) -> str:
    """Extract clean text content from HTML.
    
    Args:
        html: HTML content to extract text from
        
    Returns:
        Clean text content
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get text and clean it
    text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def extract_structured_content(html: str) -> Dict:
    """Extract structured content from HTML.
    
    Args:
        html: HTML content to extract from
        
    Returns:
        Dictionary with structured content
    """
    if not html:
        return {"title": "", "headings": [], "paragraphs": [], "lists": []}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    elif soup.h1:
        title = soup.h1.get_text(strip=True)
    
    # Extract headings
    headings = []
    for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        for heading in soup.find_all(heading_tag):
            headings.append({
                'level': heading_tag,
                'text': heading.get_text(strip=True)
            })
    
    # Extract paragraphs
    paragraphs = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)
    
    # Extract lists
    lists = []
    for ul in soup.find_all(['ul', 'ol']):
        list_items = []
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            if text:
                list_items.append(text)
        if list_items:
            lists.append({
                'type': ul.name,
                'items': list_items
            })
    
    return {
        'title': title,
        'headings': headings,
        'paragraphs': paragraphs,
        'lists': lists
    }


def process_html_content(html_content: str) -> Dict:
    """Process HTML content and return cleaned and structured data.
    
    Args:
        html_content: Raw HTML content from scraper
        
    Returns:
        Dictionary with cleaned and structured content
    """
    # Clean the HTML
    cleaned_html = clean_html(html_content)
    
    # Extract text content
    text_content = extract_text_content(cleaned_html)
    
    # Extract structured content
    structured_content = extract_structured_content(cleaned_html)
    
    # Use parsing utility to extract description
    description = extract_description(text_content)
    
    return {
        'cleaned_html': cleaned_html,
        'text_content': text_content,
        'description': description,
        'structured_content': structured_content,
        'word_count': len(text_content.split()),
        'char_count': len(text_content)
    }


def clean_and_format_html(html_content: str) -> str:
    """Clean HTML and format for markdown conversion.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Formatted clean HTML ready for markdown conversion
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    unwanted_tags = [
        'script', 'style', 'nav', 'header', 'footer', 
        'aside', 'iframe', 'noscript', 'meta', 'link',
        'svg', 'canvas', 'embed', 'object'
    ]
    
    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()
    
    # Clean attributes but keep essential ones
    for element in soup.find_all():
        if element.name in ['a', 'img']:
            # Keep href and src attributes
            attrs_to_keep = {}
            if element.name == 'a' and element.get('href'):
                attrs_to_keep['href'] = element.get('href')
            if element.name == 'img' and element.get('src'):
                attrs_to_keep['src'] = element.get('src')
            if element.name == 'img' and element.get('alt'):
                attrs_to_keep['alt'] = element.get('alt')
            element.attrs = attrs_to_keep
        else:
            element.attrs = {}
    
    # Format the HTML
    formatted_html = soup.prettify()
    
    return formatted_html 