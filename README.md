# Smart Web Scraper & File Downloader

A Python tool that intelligently processes URLs by either scraping HTML content from webpages or downloading files directly to AWS S3 storage.

## How It Works

The scraper **automatically detects** what type of content a URL contains:

### 📄 **File Detection & Download**
When you provide a URL, the system:
1. **Checks file extension** - Looks for downloadable formats (.pdf, .doc, .zip, images, etc.)
2. **Checks content type** - Makes a HEAD request to verify the actual content type
3. **Routes to downloader** - If it's a file, downloads directly to S3 storage

### 🌐 **Web Scraping**
If the URL is a regular webpage, the system:
1. **Opens browser** - Uses Playwright for JavaScript-heavy sites
2. **Loads content** - Scrolls to load lazy-loaded/dynamic content
3. **Extracts HTML** - Gets complete HTML after all content loads

## Supported File Types

**Documents**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
**Archives**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`
**Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`
**Videos**: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`
**Audio**: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`
**Data**: `.txt`, `.csv`, `.json`, `.xml`, `.sql`

## Features

- **Smart URL Detection**: Automatically determines if URL is a file or webpage
- **AWS S3 Integration**: Downloads files directly to S3 with proper metadata
- **Browser Emulation**: Uses Playwright for JavaScript-heavy websites
- **Dynamic Content Loading**: Scrolls to load lazy-loaded content
- **Session Management**: Maintains browser state across operations
- **Content-Type Verification**: Double-checks files via HTTP headers
- **Error Handling**: Graceful fallbacks and detailed error messages

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Configure AWS credentials (for file downloads):
```bash
# Set environment variables or configure AWS CLI
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

4. Update S3 configuration in `file_downloader.py`:
```python
S3_BUCKET_NAME = "your-bucket-name"
S3_REGION = "us-east-1"
```

## Usage

### Basic Usage

Run the scraper:
```bash
python3 scap.py
```

### Testing File Detection

Test the file detection system:
```bash
python3 test_file_downloader.py
```

### Configuration

Edit the configuration variables at the top of `scap.py`:

```python
WEBSITE_URL = "https://news.ycombinator.com"  # Target website
SESSION_ID = "scrape_session"                 # Browser session ID
HEADLESS_MODE = True                          # Hide browser window
PAGE_TIMEOUT = 60000                          # Page load timeout (ms)
SCROLL_TIMEOUT = 30000                        # Scroll timeout (ms)
SCROLL_DELAY = 2.0                           # Wait after scrolling (s)
WAIT_FOR_ELEMENT = "css:body"                # Element to wait for
```

### Example Workflow

```python
# URL Processing Examples:

# 1. PDF File → Downloads to S3
"https://example.com/document.pdf"
# Output: File detected → Downloaded to S3 → Returns S3 URL

# 2. Regular Webpage → Scrapes HTML
"https://news.ycombinator.com"
# Output: Webpage detected → Opens browser → Scrolls → Returns HTML

# 3. Image → Downloads to S3
"https://example.com/image.jpg"
# Output: Image detected → Downloaded to S3 → Returns metadata
```

### Functions

#### Main Functions
- **`check_if_downloadable(url)`** - Determines if URL is a downloadable file
- **`navigate_to_page(url, session_id)`** - Navigate to webpage
- **`scroll_to_bottom(crawler, url, session_id)`** - Scroll to load content
- **`get_outer_html(crawler, url, session_id)`** - Extract complete HTML

#### File Download Functions
- **`process_file_download(url)`** - Download file to S3
- **`is_downloadable_file(url)`** - Check by file extension
- **`check_content_type(url)`** - Verify by HTTP headers

### Example Output

**For a webpage:**
```
🌐 Processing as webpage: https://news.ycombinator.com
✓ Navigated to: https://news.ycombinator.com (Status: 200)
✓ Scrolled to bottom
✓ Got HTML (37461 chars)
```

**For a file:**
```
📁 Detected downloadable file: https://example.com/document.pdf
✓ Downloaded file to S3:
  S3 URL: https://your-bucket.s3.us-east-1.amazonaws.com/downloads/document.pdf
  File size: 245760 bytes
  Content type: application/pdf
```

## File Structure

```
myscapper/
├── scap.py                    # Main scraper with URL routing logic
├── file_downloader.py         # File detection and S3 download functionality
├── test_file_downloader.py    # Test suite for file detection
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Requirements

- Python 3.7+
- crawl4ai
- playwright
- psutil
- boto3 (for S3 downloads)
- aiohttp (for HTTP requests)

## AWS Configuration

To enable file downloads, you need:
1. AWS account with S3 access
2. AWS credentials configured
3. S3 bucket created
4. Update `S3_BUCKET_NAME` and `S3_REGION` in `file_downloader.py`

## License

MIT License 