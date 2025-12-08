# Email Agent

AI-powered email agent for managing and responding to emails.

## Features

- Email reading and parsing
- Automated email responses
- Email categorization
- Smart email routing

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Copy `.env.example` to `.env` and fill in values.

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/email/process` - Process an email
- `POST /api/email/respond` - Generate email response
- `GET /api/email/history` - Get email history

## Development

Run tests:
```bash
pytest
```

Run with hot reload:
```bash
uvicorn app.main:app --reload --port 8081
```

