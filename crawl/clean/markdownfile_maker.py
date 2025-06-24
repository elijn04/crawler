"""
Markdown File Maker Module
Converts cleaned HTML content to markdown format.
"""

import re
import os
from bs4 import BeautifulSoup
from typing import Dict, Optional
from datetime import datetime
from crawl.clean.html_cleaner import clean_and_format_html, extract_structured_content


def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown format.
    
    Args:
        html_content: Cleaned HTML content
        
    Returns:
        Markdown formatted content
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    markdown_content = ""
    
    # Process each element
    for element in soup.find_all():
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Convert headings
            level = int(element.name[1])
            heading_text = element.get_text(strip=True)
            markdown_content += f"{'#' * level} {heading_text}\n\n"
            
        elif element.name == 'p':
            # Convert paragraphs
            text = element.get_text(strip=True)
            if text:
                markdown_content += f"{text}\n\n"
                
        elif element.name == 'a':
            # Convert links
            text = element.get_text(strip=True)
            href = element.get('href', '#')
            if text and href:
                markdown_content += f"[{text}]({href})"
                
        elif element.name == 'img':
            # Convert images
            alt = element.get('alt', 'Image')
            src = element.get('src', '')
            if src:
                markdown_content += f"![{alt}]({src})\n\n"
                
        elif element.name in ['ul', 'ol']:
            # Convert lists
            markdown_content += convert_list_to_markdown(element)
            
        elif element.name in ['strong', 'b']:
            # Convert bold text
            text = element.get_text(strip=True)
            if text:
                markdown_content += f"**{text}**"
                
        elif element.name in ['em', 'i']:
            # Convert italic text
            text = element.get_text(strip=True)
            if text:
                markdown_content += f"*{text}*"
                
        elif element.name == 'code':
            # Convert inline code
            text = element.get_text(strip=True)
            if text:
                markdown_content += f"`{text}`"
                
        elif element.name == 'pre':
            # Convert code blocks
            text = element.get_text(strip=True)
            if text:
                markdown_content += f"```\n{text}\n```\n\n"
                
        elif element.name == 'blockquote':
            # Convert blockquotes
            text = element.get_text(strip=True)
            if text:
                lines = text.split('\n')
                quoted_lines = [f"> {line}" for line in lines if line.strip()]
                markdown_content += '\n'.join(quoted_lines) + "\n\n"
                
        elif element.name == 'hr':
            # Convert horizontal rules
            markdown_content += "---\n\n"
            
        elif element.name == 'br':
            # Convert line breaks
            markdown_content += "\n"
    
    # Clean up extra whitespace
    markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
    markdown_content = markdown_content.strip()
    
    return markdown_content


def convert_list_to_markdown(list_element) -> str:
    """Convert HTML list to markdown format.
    
    Args:
        list_element: BeautifulSoup list element (ul or ol)
        
    Returns:
        Markdown formatted list
    """
    markdown_list = ""
    is_ordered = list_element.name == 'ol'
    
    for i, li in enumerate(list_element.find_all('li', recursive=False), 1):
        text = li.get_text(strip=True)
        if text:
            if is_ordered:
                markdown_list += f"{i}. {text}\n"
            else:
                markdown_list += f"- {text}\n"
    
    return markdown_list + "\n"


def create_markdown_header(title: str, url: str = "", description: str = "") -> str:
    """Create markdown header with metadata.
    
    Args:
        title: Page title
        url: Source URL
        description: Page description
        
    Returns:
        Formatted markdown header
    """
    header = f"# {title}\n\n"
    
    if url:
        header += f"**Source URL:** {url}\n\n"
    
    if description:
        header += f"**Description:** {description}\n\n"
    
    header += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    header += "---\n\n"
    
    return header


def convert_html_to_markdown_file(html_content: str, output_path: str, 
                                 title: str = "", url: str = "", 
                                 description: str = "") -> str:
    """Convert HTML content to markdown and save to file.
    
    Args:
        html_content: Raw HTML content to convert
        output_path: Path to save markdown file
        title: Page title for header
        url: Source URL for header
        description: Page description for header
        
    Returns:
        Path to saved markdown file
    """
    # Clean and format HTML for conversion
    cleaned_html = clean_and_format_html(html_content)
    
    # Extract structured content for better title/description
    if not title or not description:
        structured = extract_structured_content(cleaned_html)
        if not title and structured.get('title'):
            title = structured['title']
        if not description and structured.get('paragraphs'):
            description = structured['paragraphs'][0][:200] + "..." if len(structured['paragraphs'][0]) > 200 else structured['paragraphs'][0]
    
    # Convert to markdown
    markdown_content = html_to_markdown(cleaned_html)
    
    # Add header
    header = create_markdown_header(title or "Untitled", url, description)
    full_markdown = header + markdown_content
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
    
    return output_path


def process_scraped_html_to_markdown(scraped_result: Dict, output_dir: str = "markdown_output") -> str:
    """Process scraped HTML result and convert to markdown file.
    
    Args:
        scraped_result: Result from scraper with HTML content
        output_dir: Directory to save markdown files
        
    Returns:
        Path to generated markdown file
    """
    if not scraped_result.get('html_content'):
        raise ValueError("No HTML content found in scraped result")
    
    # Extract info from scraped result
    url = scraped_result.get('url', '')
    html_content = scraped_result['html_content']
    
    # Create filename from URL
    filename = create_filename_from_url(url)
    output_path = os.path.join(output_dir, f"{filename}.md")
    
    # Convert to markdown file
    return convert_html_to_markdown_file(
        html_content=html_content,
        output_path=output_path,
        url=url
    )


def create_filename_from_url(url: str) -> str:
    """Create safe filename from URL.
    
    Args:
        url: Source URL
        
    Returns:
        Safe filename string
    """
    if not url:
        return f"webpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Extract domain and path
    filename = re.sub(r'https?://', '', url)
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename or f"webpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def batch_convert_html_to_markdown(html_files: list, output_dir: str = "markdown_output") -> list:
    """Convert multiple HTML files to markdown.
    
    Args:
        html_files: List of HTML file paths or content
        output_dir: Directory to save markdown files
        
    Returns:
        List of generated markdown file paths
    """
    markdown_files = []
    
    for i, html_content in enumerate(html_files):
        if isinstance(html_content, str) and os.path.isfile(html_content):
            # Read from file
            with open(html_content, 'r', encoding='utf-8') as f:
                content = f.read()
            filename = os.path.splitext(os.path.basename(html_content))[0]
        else:
            # Direct content
            content = html_content
            filename = f"document_{i+1}"
        
        output_path = os.path.join(output_dir, f"{filename}.md")
        markdown_path = convert_html_to_markdown_file(content, output_path)
        markdown_files.append(markdown_path)
    
    return markdown_files 