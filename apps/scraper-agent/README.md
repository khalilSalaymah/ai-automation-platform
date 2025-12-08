# Scraper Agent

Web scraping agent with AI-powered content extraction.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Copy `.env.example` to `.env` and fill in values.

3. Run:
```bash
uvicorn app.main:app --reload
```

## API

- `GET /health` - Health check
- `POST /api/scraper/scrape` - Scrape a URL

