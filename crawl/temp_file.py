"""
Temporary File Manager Module
Handles creation and management of temporary files for documents and webpages.
"""

import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from .clean.html_cleaner import process_html_content
from .clean.markdownfile_maker import convert_html_to_markdown_file


class TempFileManager:
    """Manages temporary files for the scraping workflow."""
    
    def __init__(self):
        """Initialize with a temporary directory for this session."""
        self.temp_dir = tempfile.mkdtemp(prefix="myscapper_")
        self.file_counter = 0
        print(f"📁 Created temporary directory: {self.temp_dir}")
    
    def create_temp_document(self, source_path: str, original_filename: str) -> Optional[str]:
        """Create temporary copy of a downloaded document.
        
        Args:
            source_path: Path to the original downloaded file
            original_filename: Original filename to preserve
            
        Returns:
            Path to temporary file, or None if creation failed
        """
        if not source_path or not os.path.exists(source_path):
            return None
        
        try:
            self.file_counter += 1
            temp_file_path = os.path.join(self.temp_dir, f"doc_{self.file_counter}_{original_filename}")
            
            # Copy to temp directory
            shutil.copy2(source_path, temp_file_path)
            print(f"📄 Created temp document: {temp_file_path}")
            
            # Clean up original download
            try:
                os.remove(source_path)
            except OSError:
                pass
            
            return temp_file_path
            
        except Exception as e:
            print(f"⚠️  Error creating temp document: {e}")
            return None
    
    def create_temp_markdown(self, html_content: str, url: str) -> Optional[str]:
        """Create temporary markdown file from HTML content.
        
        Args:
            html_content: Raw HTML content to convert
            url: Source URL for metadata
            
        Returns:
            Path to temporary markdown file, or None if creation failed
        """
        if not html_content:
            return None
        
        try:
            # Process HTML to get cleaned data
            cleaned_data = process_html_content(html_content)
            
            self.file_counter += 1
            temp_md_path = os.path.join(self.temp_dir, f"webpage_{self.file_counter}.md")
            
            # Extract title for better filename
            title = cleaned_data['structured_content'].get('title', 'Untitled')
            if title and title != 'Untitled':
                safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                temp_md_path = os.path.join(self.temp_dir, f"webpage_{self.file_counter}_{safe_title.replace(' ', '_')}.md")
            
            # Convert to markdown
            convert_html_to_markdown_file(
                html_content=html_content,
                output_path=temp_md_path,
                title=title,
                url=url,
                description=cleaned_data.get('description', '')
            )
            
            print(f"📄 Created temp markdown: {temp_md_path}")
            return temp_md_path
            
        except Exception as e:
            print(f"⚠️  Markdown conversion failed: {e}")
            return None
    
    def get_temp_dir(self) -> str:
        """Get the temporary directory path."""
        return self.temp_dir
    
    def cleanup(self) -> None:
        """Clean up the temporary directory and all files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"🗑️  Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"⚠️  Error cleaning up temp directory: {e}")


# Standalone functions for backward compatibility
def create_temp_document_file(source_path: str, original_filename: str, temp_dir: str) -> Optional[str]:
    """Create temporary copy of a downloaded document.
    
    Args:
        source_path: Path to the original downloaded file
        original_filename: Original filename to preserve
        temp_dir: Directory to create temp file in
        
    Returns:
        Path to temporary file, or None if creation failed
    """
    if not source_path or not os.path.exists(source_path) or not temp_dir:
        return None
    
    try:
        temp_file_path = os.path.join(temp_dir, original_filename)
        
        # Copy to temp directory
        shutil.copy2(source_path, temp_file_path)
        print(f"📄 Created temp document: {temp_file_path}")
        
        # Clean up original download
        try:
            os.remove(source_path)
        except OSError:
            pass
        
        return temp_file_path
        
    except Exception as e:
        print(f"⚠️  Error creating temp document: {e}")
        return None


def create_temp_markdown_file(html_content: str, url: str, temp_dir: str) -> Optional[str]:
    """Create temporary markdown file from HTML content.
    
    Args:
        html_content: Raw HTML content to convert
        url: Source URL for metadata
        temp_dir: Directory to create temp file in
        
    Returns:
        Path to temporary markdown file, or None if creation failed
    """
    if not html_content or not temp_dir:
        return None
    
    try:
        # Process HTML to get cleaned data
        cleaned_data = process_html_content(html_content)
        
        # Create temp markdown filename
        temp_md_path = os.path.join(temp_dir, "webpage.md")
        
        # Extract title for better filename
        title = cleaned_data['structured_content'].get('title', 'Untitled')
        if title and title != 'Untitled':
            safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            temp_md_path = os.path.join(temp_dir, f"{safe_title.replace(' ', '_')}.md")
        
        # Convert to markdown
        convert_html_to_markdown_file(
            html_content=html_content,
            output_path=temp_md_path,
            title=title,
            url=url,
            description=cleaned_data.get('description', '')
        )
        
        print(f"📄 Created temp markdown: {temp_md_path}")
        return temp_md_path
        
    except Exception as e:
        print(f"⚠️  Markdown conversion failed: {e}")
        return None


def cleanup_temp_directory(temp_dir: str) -> None:
    """Clean up a temporary directory and all files.
    
    Args:
        temp_dir: Path to temporary directory to clean up
    """
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            print(f"🗑️  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️  Error cleaning up temp directory: {e}") 