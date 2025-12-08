# AIOps Bot

AI-powered operations bot for system monitoring and analysis.

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
- `POST /api/aiops/analyze` - Analyze system metrics

