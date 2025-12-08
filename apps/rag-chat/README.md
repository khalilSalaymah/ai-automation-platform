# RAG Chat

Retrieval-Augmented Generation chat application with document Q&A.

## Features

- Document upload and indexing
- Semantic search over documents
- Context-aware chat responses
- Support for PGVector and Pinecone

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
- `POST /api/chat` - Chat with RAG
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents

