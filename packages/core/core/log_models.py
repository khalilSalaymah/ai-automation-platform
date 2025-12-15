"""Database models for log entries."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, String, Text, JSON, Index
from sqlalchemy import DateTime, func


class LogEntry(SQLModel, table=True):
    """Log entry database model for querying and filtering."""

    __tablename__ = "log_entries"
    __table_args__ = (
        Index("idx_trace_id", "trace_id"),
        Index("idx_span_id", "span_id"),
        Index("idx_timestamp", "timestamp"),
        Index("idx_level", "level"),
        Index("idx_service", "service"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), index=True),
    )
    level: str = Field(index=True)  # INFO, ERROR, WARNING, etc.
    message: str = Field(sa_column=Column(Text))
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    
    # Trace context
    trace_id: Optional[str] = Field(default=None, index=True)
    span_id: Optional[str] = Field(default=None, index=True)
    parent_span_id: Optional[str] = None
    
    # Operation context
    operation: Optional[str] = None  # llm_call, tool_execution, http_request
    service: Optional[str] = None  # openai, tool_registry, gateway
    
    # Additional metadata (stored as JSON). "metadata" is reserved by SQLAlchemy's Declarative API,
    # so we use a different attribute name and map it to the "metadata" column.
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column("metadata", JSON))
    
    # Error information
    error_type: Optional[str] = None
    error_value: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_traceback: Optional[str] = Field(default=None, sa_column=Column(Text))


class LogEntryResponse(SQLModel):
    """Log entry response model."""

    id: int
    timestamp: datetime
    level: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    operation: Optional[str] = None
    service: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_type: Optional[str] = None
    error_value: Optional[str] = None
    error_traceback: Optional[str] = None


class LogQueryParams(SQLModel):
    """Log query parameters."""

    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    level: Optional[str] = None
    operation: Optional[str] = None
    service: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
