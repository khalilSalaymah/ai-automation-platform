"""Scheduler and task queue models."""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum
from sqlmodel import SQLModel, Field, Column, String, JSON
from sqlalchemy import DateTime, func, Text


class TaskStatus(str, PyEnum):
    """Task execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask(SQLModel, table=True):
    """Scheduled task definition."""

    __tablename__ = "scheduled_tasks"

    id: Optional[str] = Field(default=None, primary_key=True)
    agent_name: str = Field(index=True)  # e.g., "email-agent", "aiops-bot"
    task_name: str = Field(index=True)  # Unique task name within agent
    description: Optional[str] = None
    enabled: bool = Field(default=True)
    schedule: str = Field()  # Cron expression or interval
    task_type: str = Field()  # "cron" or "interval"
    function_path: str = Field()  # e.g., "app.services.email_service:process_scheduled"
    args: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    kwargs: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class TaskExecution(SQLModel, table=True):
    """Task execution record."""

    __tablename__ = "task_executions"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)  # RQ job ID
    scheduled_task_id: Optional[str] = Field(default=None, index=True)  # Reference to ScheduledTask
    agent_name: str = Field(index=True)
    task_name: str = Field(index=True)
    status: TaskStatus = Field(default=TaskStatus.QUEUED, index=True)
    function_path: str = Field()
    args: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    kwargs: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    result: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class ScheduledTaskCreate(SQLModel):
    """Create scheduled task request."""

    agent_name: str
    task_name: str
    description: Optional[str] = None
    enabled: bool = True
    schedule: str
    task_type: str  # "cron" or "interval"
    function_path: str
    args: Optional[Dict[str, Any]] = None
    kwargs: Optional[Dict[str, Any]] = None


class ScheduledTaskResponse(SQLModel):
    """Scheduled task response."""

    id: str
    agent_name: str
    task_name: str
    description: Optional[str]
    enabled: bool
    schedule: str
    task_type: str
    function_path: str
    args: Optional[Dict[str, Any]]
    kwargs: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class TaskExecutionResponse(SQLModel):
    """Task execution response."""

    id: str
    task_id: str
    scheduled_task_id: Optional[str]
    agent_name: str
    task_name: str
    status: TaskStatus
    function_path: str
    args: Optional[Dict[str, Any]]
    kwargs: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class EventMessage(SQLModel):
    """Event bus message."""

    event_type: str
    source_agent: str
    target_agent: Optional[str] = None  # None for broadcast
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

