"""Knowledge base database models."""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, String, Text, JSON
from sqlalchemy import DateTime, func, ForeignKey
from enum import Enum as PyEnum


class DocumentSource(PyEnum):
    """Document source types."""

    UPLOAD = "upload"
    URL = "url"
    NOTION = "notion"


class DocumentStatus(PyEnum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(SQLModel, table=True):
    """Document model for knowledge base."""

    __tablename__ = "documents"

    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    source: DocumentSource
    source_url: Optional[str] = None  # For URL/Notion sources
    file_path: Optional[str] = None  # For uploaded files
    file_type: Optional[str] = None  # MIME type or extension
    file_size: Optional[int] = None  # Size in bytes
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    total_chunks: int = Field(default=0)
    processed_chunks: int = Field(default=0)
    error_message: Optional[str] = None
    org_id: Optional[str] = Field(default=None, index=True)  # Multi-tenant support
    user_id: Optional[str] = Field(default=None, index=True)  # Creator
    # Additional metadata for the document (stored as JSON)
    extra_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class DocumentChunk(SQLModel, table=True):
    """Document chunk model."""

    __tablename__ = "document_chunks"

    id: Optional[str] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    chunk_index: int  # Order within document
    content: str = Field(sa_column=Column(Text))
    vector_id: Optional[str] = None  # ID in vector store
    # Additional metadata for the chunk (stored as JSON)
    extra_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )


class AgentDocument(SQLModel, table=True):
    """Association table for agents and documents."""

    __tablename__ = "agent_documents"

    id: Optional[str] = Field(default=None, primary_key=True)
    agent_name: str = Field(index=True)  # Agent identifier
    document_id: str = Field(foreign_key="documents.id", index=True)
    org_id: Optional[str] = Field(default=None, index=True)  # Multi-tenant support
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )


# Request/Response models
class DocumentCreate(SQLModel):
    """Document creation model."""

    name: str
    source: DocumentSource
    source_url: Optional[str] = None
    org_id: Optional[str] = None


class DocumentResponse(SQLModel):
    """Document response model."""

    id: str
    name: str
    source: DocumentSource
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: DocumentStatus
    total_chunks: int
    processed_chunks: int
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class DocumentSearchRequest(SQLModel):
    """Document search request."""

    query: str
    top_k: int = 10
    document_ids: Optional[List[str]] = None  # Filter by specific documents
    agent_name: Optional[str] = None  # Filter by agent


class DocumentSearchResult(SQLModel):
    """Document search result."""

    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    chunk_index: int
    metadata: Optional[dict] = None


class AgentDocumentLink(SQLModel):
    """Link document to agent."""

    agent_name: str
    document_ids: List[str]


class AgentDocumentResponse(SQLModel):
    """Agent document response."""

    agent_name: str
    documents: List[DocumentResponse]
