# Integration Guide

## Setup AWS (optional)
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
```

## Feed Links
```python
from agent_flow_link_scrapper import scrape_urls

results = scrape_urls(['https://example.com'])
```

## Get HTML Text
```python
html_text = results['https://example.com']['html_content']
```

## Done. 