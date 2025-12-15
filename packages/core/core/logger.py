"""Structured JSON logging with trace_id and span tracking."""

import sys
import json
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

# Context variables for trace_id and span_id
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
parent_span_id_var: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)

# Remove default handler
logger.remove()


def serialize_log(record: Dict[str, Any]) -> str:
    """Serialize log record to JSON."""
    log_data = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add trace context if available
    trace_id = trace_id_var.get()
    span_id = span_id_var.get()
    parent_span_id = parent_span_id_var.get()
    
    if trace_id:
        log_data["trace_id"] = trace_id
    if span_id:
        log_data["span_id"] = span_id
    if parent_span_id:
        log_data["parent_span_id"] = parent_span_id
    
    # Add extra fields from record
    if "extra" in record:
        for key, value in record["extra"].items():
            if key not in ["trace_id", "span_id", "parent_span_id"]:
                log_data[key] = value
    
    # Add exception info if present
    exc = record.get("exception")
    if exc is not None:
        log_data["exception"] = {
            "type": exc.type.__name__ if getattr(exc, "type", None) else None,
            "value": str(getattr(exc, "value", None)) if getattr(exc, "value", None) else None,
            "traceback": getattr(exc, "traceback", None) if getattr(exc, "traceback", None) else None,
        }
    
    return json.dumps(log_data, default=str)


# Add JSON structured handler for stdout
logger.add(
    sys.stdout,
    format=serialize_log,
    level="INFO",
    serialize=True,
)

# Add JSON structured file handler for all logs
logger.add(
    "logs/app.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO",
    format=serialize_log,
    serialize=True,
)

# Add JSON structured file handler for errors
logger.add(
    "logs/error.log",
    rotation="10 MB",
    retention="90 days",
    level="ERROR",
    format=serialize_log,
    serialize=True,
)


def get_trace_id() -> Optional[str]:
    """Get current trace_id from context."""
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str]) -> None:
    """Set trace_id in context."""
    trace_id_var.set(trace_id)


def generate_trace_id() -> str:
    """Generate a new trace_id."""
    return str(uuid.uuid4())


def get_span_id() -> Optional[str]:
    """Get current span_id from context."""
    return span_id_var.get()


def set_span_id(span_id: Optional[str], parent_span_id: Optional[str] = None) -> None:
    """Set span_id and parent_span_id in context."""
    span_id_var.set(span_id)
    if parent_span_id:
        parent_span_id_var.set(parent_span_id)


def generate_span_id() -> str:
    """Generate a new span_id."""
    return str(uuid.uuid4())


def log_span(
    operation: str,
    service: str,
    metadata: Optional[Dict[str, Any]] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    error: Optional[str] = None,
):
    """
    Log a span (operation tracking).
    
    Args:
        operation: Operation name (e.g., "llm_call", "tool_execution")
        service: Service name (e.g., "openai", "tool_registry")
        metadata: Additional metadata
        start_time: Start timestamp
        end_time: End timestamp
        error: Error message if operation failed
    """
    span_id = get_span_id()
    parent_span_id = parent_span_id_var.get()
    trace_id = get_trace_id()
    
    span_data = {
        "span_type": "operation",
        "operation": operation,
        "service": service,
        "span_id": span_id,
        "trace_id": trace_id,
    }
    
    if parent_span_id:
        span_data["parent_span_id"] = parent_span_id
    
    if start_time and end_time:
        span_data["duration_ms"] = (end_time - start_time) * 1000
    
    if metadata:
        span_data.update(metadata)
    
    if error:
        span_data["error"] = error
        logger.error("Span completed with error", **span_data)
    else:
        logger.info("Span completed", **span_data)


__all__ = [
    "logger",
    "get_trace_id",
    "set_trace_id",
    "generate_trace_id",
    "get_span_id",
    "set_span_id",
    "generate_span_id",
    "log_span",
]

