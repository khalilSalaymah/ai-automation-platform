"""RAG data models."""

from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    sources: List[str] = []


class DocumentInfo(BaseModel):
    """Document information."""
    id: str
    filename: str
    indexed_at: str

