# AgentFlow Link Scrapper

**Intelligent web scraping and file downloading tool** that automatically detects whether to scrape web content or download files from URLs. Built with Crawl4AI for powerful browser automation and smart content extraction.

## What It Does

AgentFlow Link Scrapper is a Python library that processes URLs intelligently:

- **🌐 Web Scraping**: Extracts full HTML content from websites using real browser automation
- **📁 File Downloads**: Automatically detects and downloads PDFs, documents, images, and other files
- **🤖 Login Detection**: Identifies authentication-protected pages and provides helpful guidance
- **☁️ AWS S3 Integration**: Optional cloud storage for downloaded files
- **🔍 Smart Content Type Detection**: Uses both file extensions and HTTP headers to make intelligent routing decisions

## What is Crawl4AI?

[Crawl4AI](https://github.com/unclecode/crawl4ai) is a powerful web crawling and data extraction library that provides:

- **Real Browser Automation**: Uses Playwright for JavaScript-heavy sites
- **Anti-Bot Protection**: Handles modern web protection mechanisms
- **Session Management**: Maintains browser sessions for complex workflows
- **Dynamic Content Loading**: Automatically scrolls and waits for content to load
- **Intelligent Extraction**: Extracts clean text and structured data from web pages

## Core Features

### 🎯 Intelligent URL Processing
- Automatically detects file types (PDF, DOC, images, etc.) vs web pages
- Routes to appropriate handler (download vs scrape)
- Handles redirects and dynamic content

### 🔐 Authentication Detection
- Identifies login/paywall pages
- Provides clear guidance for protected content
- Detects subscription requirements

### 📦 File Download Support
- **Local Storage**: Downloads to local `downloads/` folder
- **AWS S3**: Optional cloud storage with automatic uploads
- **Multiple Formats**: PDFs, Office docs, images, archives, data files

### 🚀 Easy Integration
- Simple Python API for single or batch processing
- JSON output for integration with other systems
- Async/await support for high performance

## Installation

### Quick Setup
```bash
./setup.sh
```

### Manual Setup
```bash
pip install -r requirements.txt
playwright install
```

## Configuration

### AWS S3 (Optional)
Create `.env` file for cloud storage:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1
```

## Usage

### Basic Usage
```python
from agent_flow_link_scrapper import scrape_urls

# Process multiple URLs
results = scrape_urls([
    'https://example.com',           # Web page → scrapes HTML
    'https://example.com/doc.pdf',   # File → downloads
    'https://news.ycombinator.com'   # Web page → scrapes HTML
])

# Access scraped HTML content
html_content = results['https://example.com']['html_content']

# Check download results
pdf_result = results['https://example.com/doc.pdf']['result']
```

### Advanced Usage
```python
from agent_flow_link_scrapper import AgentFlowLinkScrapper

# Initialize with AWS credentials
scrapper = AgentFlowLinkScrapper(
    aws_access_key='your_key',
    aws_secret_key='your_secret',
    s3_bucket='your_bucket'
)

# Process URLs with file saving
results = scrapper.process_urls(
    ['https://example.com', 'https://site.com/file.pdf'],
    save_file='my_results.json'
)

# Get summary statistics
summary = scrapper.get_summary(results)
print(f"Success rate: {summary['success_rate']}%")
```

### Single URL Processing
```python
from agent_flow_link_scrapper import scrape_url

# Process single URL
result = scrape_url('https://example.com')
if result['status'] == 'success':
    print(f"HTML length: {result['html_length']} chars")
```

## Core Functions

### Main Functions
- `scrape_urls(urls)` - Process multiple URLs
- `scrape_url(url)` - Process single URL  
- `configure_aws()` - Set up S3 credentials

### Class Methods
- `AgentFlowLinkScrapper.process_urls()` - Batch processing
- `AgentFlowLinkScrapper.process_url()` - Single URL processing
- `AgentFlowLinkScrapper.get_summary()` - Statistics and success rates

## Output Format

### Successful Web Scraping
```json
{
  "https://example.com": {
    "status": "success",
    "type": "webpage",
    "url": "https://example.com",
    "status_code": 200,
    "html_content": "<html>...</html>",
    "html_length": 15420
  }
}
```

### Successful File Download
```json
{
  "https://example.com/file.pdf": {
    "status": "download_success", 
    "type": "file_download",
    "result": {
      "success": true,
      "filename": "file.pdf",
      "local_path": "downloads/file.pdf",
      "s3_url": "https://bucket.s3.amazonaws.com/file.pdf"
    }
  }
}
```

### Failed Processing
```json
{
  "https://protected-site.com": {
    "status": "failed",
    "type": "webpage", 
    "error_type": "login_required",
    "error": "Authentication required to access this content"
  }
}
```

## Supported File Types

**Documents**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX  
**Archives**: ZIP, RAR, 7Z, TAR, GZ  
**Images**: JPG, PNG, GIF, BMP, TIFF  
**Media**: MP4, AVI, MP3, WAV  
**Data**: CSV, JSON, XML, TXT  

## Error Handling

The scrapper handles common issues:
- **Login Required**: Detects authentication pages
- **Rate Limiting**: Handles anti-bot protection  
- **Network Errors**: Robust retry mechanisms
- **Invalid URLs**: Clear error messages
- **File Access Issues**: Permissions and storage errors

## Integration Examples

### Batch Processing
```python
urls = [
    'https://news.ycombinator.com',
    'https://example.com/report.pdf', 
    'https://api.example.com/data.json'
]

results = scrape_urls(urls, save_file='batch_results.json')
```

### Content Analysis
```python
result = scrape_url('https://example.com')
if result['status'] == 'success':
    html = result['html_content']
    # Parse with BeautifulSoup, extract data, etc.
```

## Requirements

- Python 3.7+
- Playwright (auto-installed)
- AWS account (optional, for S3 storage)

## License

MIT License 