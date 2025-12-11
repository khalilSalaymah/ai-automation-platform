"""Log viewing API router."""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select, and_, or_
from .database import get_session
from .log_models import LogEntry, LogEntryResponse, LogQueryParams
from .dependencies import RequireAdmin
from .logger import logger

router = APIRouter(prefix="/api/admin/logs", tags=["logs"])


def parse_log_line(line: str) -> Optional[dict]:
    """Parse a JSON log line."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def read_log_file(file_path: str, limit: int = 100, offset: int = 0) -> List[dict]:
    """
    Read log entries from a log file.
    
    Args:
        file_path: Path to log file
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        
    Returns:
        List of log entries
    """
    if not os.path.exists(file_path):
        return []
    
    entries = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read all lines and parse
            all_entries = []
            for line in f:
                entry = parse_log_line(line)
                if entry:
                    all_entries.append(entry)
            
            # Apply offset and limit
            entries = all_entries[offset:offset + limit]
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")
    
    return entries


@router.get("/", response_model=List[LogEntryResponse])
async def get_logs(
    trace_id: Optional[str] = Query(None),
    span_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source: str = Query("database", regex="^(database|file|both)$"),
    session: Session = Depends(get_session),
    _: None = Depends(RequireAdmin),
):
    """
    Get log entries with filtering.
    
    Args:
        trace_id: Filter by trace ID
        span_id: Filter by span ID
        level: Filter by log level (INFO, ERROR, WARNING, etc.)
        operation: Filter by operation type (llm_call, tool_execution, http_request)
        service: Filter by service name
        start_time: Filter logs after this time
        end_time: Filter logs before this time
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        source: Source to read from (database, file, or both)
        session: Database session
        
    Returns:
        List of log entries
    """
    if source == "file" or source == "both":
        # Read from log files
        log_dir = Path("logs")
        file_entries = []
        
        # Read from app.log and error.log
        for log_file in ["app.log", "error.log"]:
            file_path = log_dir / log_file
            if file_path.exists():
                entries = read_log_file(str(file_path), limit=limit * 2, offset=0)
                file_entries.extend(entries)
        
        # Filter file entries
        filtered_entries = []
        for entry in file_entries:
            if trace_id and entry.get("trace_id") != trace_id:
                continue
            if span_id and entry.get("span_id") != span_id:
                continue
            if level and entry.get("level") != level:
                continue
            if operation and entry.get("operation") != operation:
                continue
            if service and entry.get("service") != service:
                continue
            
            # Parse timestamp
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if start_time and entry_time < start_time:
                    continue
                if end_time and entry_time > end_time:
                    continue
            except (ValueError, TypeError):
                pass
            
            filtered_entries.append(entry)
        
        # Sort by timestamp descending and apply limit/offset
        filtered_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        file_entries = filtered_entries[offset:offset + limit]
        
        if source == "file":
            # Convert file entries to LogEntryResponse, handling missing fields
            result = []
            for entry in file_entries:
                try:
                    result.append(LogEntryResponse.model_validate(entry))
                except Exception as e:
                    # Skip invalid entries
                    logger.warning(f"Invalid log entry: {e}")
            return result
    
    if source == "database" or source == "both":
        # Query database
        query = select(LogEntry)
        conditions = []
        
        if trace_id:
            conditions.append(LogEntry.trace_id == trace_id)
        if span_id:
            conditions.append(LogEntry.span_id == span_id)
        if level:
            conditions.append(LogEntry.level == level)
        if operation:
            conditions.append(LogEntry.operation == operation)
        if service:
            conditions.append(LogEntry.service == service)
        if start_time:
            conditions.append(LogEntry.timestamp >= start_time)
        if end_time:
            conditions.append(LogEntry.timestamp <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(LogEntry.timestamp.desc()).limit(limit).offset(offset)
        
        results = session.exec(query).all()
        
        if source == "database":
            return [LogEntryResponse.model_validate(entry) for entry in results]
        else:
            # Combine both sources
            db_entries = [LogEntryResponse.model_validate(entry).model_dump() for entry in results]
            all_entries = file_entries + db_entries
            # Sort by timestamp and deduplicate
            all_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            # Simple deduplication by timestamp and message
            seen = set()
            unique_entries = []
            for entry in all_entries:
                key = (entry.get("timestamp"), entry.get("message"))
                if key not in seen:
                    seen.add(key)
                    unique_entries.append(entry)
            # Convert to LogEntryResponse
            result = []
            for entry in unique_entries[:limit]:
                try:
                    result.append(LogEntryResponse.model_validate(entry))
                except Exception as e:
                    logger.warning(f"Invalid log entry: {e}")
            return result
    
    return []


@router.get("/trace/{trace_id}", response_model=List[LogEntryResponse])
async def get_trace_logs(
    trace_id: str,
    limit: int = Query(1000, ge=1, le=10000),
    session: Session = Depends(get_session),
    _: None = Depends(RequireAdmin),
):
    """
    Get all logs for a specific trace ID.
    
    Args:
        trace_id: Trace ID to filter by
        limit: Maximum number of entries to return
        session: Database session
        
    Returns:
        List of log entries for the trace
    """
    return await get_logs(
        trace_id=trace_id,
        limit=limit,
        source="both",
        session=session,
        _=_,
    )


@router.get("/stats")
async def get_log_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    session: Session = Depends(get_session),
    _: None = Depends(RequireAdmin),
):
    """
    Get log statistics.
    
    Args:
        start_time: Filter logs after this time
        end_time: Filter logs before this time
        session: Database session
        
    Returns:
        Log statistics
    """
    query = select(LogEntry)
    conditions = []
    
    if start_time:
        conditions.append(LogEntry.timestamp >= start_time)
    if end_time:
        conditions.append(LogEntry.timestamp <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    all_logs = session.exec(query).all()
    
    stats = {
        "total": len(all_logs),
        "by_level": {},
        "by_operation": {},
        "by_service": {},
        "error_count": 0,
        "warning_count": 0,
    }
    
    for log in all_logs:
        # Count by level
        stats["by_level"][log.level] = stats["by_level"].get(log.level, 0) + 1
        
        if log.level == "ERROR":
            stats["error_count"] += 1
        elif log.level == "WARNING":
            stats["warning_count"] += 1
        
        if log.operation:
            stats["by_operation"][log.operation] = stats["by_operation"].get(log.operation, 0) + 1
        
        if log.service:
            stats["by_service"][log.service] = stats["by_service"].get(log.service, 0) + 1
    
    return stats
