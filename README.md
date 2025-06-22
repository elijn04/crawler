# AgentFlow Link Scrapper

## Setup (2 steps)

1. **Install:**
```bash
./setup.sh
```

2. **AWS Keys (optional, for file downloads):**
Create `.env` file:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
```

## How to Use

**Feed links here:**
```python
from agent_flow_link_scrapper import scrape_urls

results = scrape_urls(['https://example.com', 'https://file.pdf'])
```

**Get HTML text here:**
```python
html_text = results['https://example.com']['html_content']
```

**That's it.** 