# Web Scraper

A simple Python web scraper that uses browser emulation to extract complete HTML content from dynamic websites.

## Features

- **Browser Emulation**: Uses Playwright to handle JavaScript-heavy sites
- **Dynamic Content Loading**: Automatically scrolls to load lazy-loaded content
- **Session Management**: Maintains browser state across operations
- **Complete HTML Extraction**: Gets the full outerHTML after all content loads
- **Easy Configuration**: All settings configurable via variables

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

## Usage

### Basic Usage

Run the scraper:
```bash
python3 scap.py
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

### Functions

The scraper provides three main functions:

1. **`navigate_to_page(url, session_id)`** - Navigate to webpage
2. **`scroll_to_bottom(crawler, url, session_id)`** - Scroll to load content
3. **`get_outer_html(crawler, url, session_id)`** - Extract complete HTML

### Example Output

```
✓ Navigated to: https://news.ycombinator.com (Status: 200)
✓ Scrolled to bottom
✓ Got HTML (37461 chars)
==================================================
<html lang="en" op="news"><head>...
```

## Requirements

- Python 3.7+
- crawl4ai
- playwright
- psutil

## License

MIT License 