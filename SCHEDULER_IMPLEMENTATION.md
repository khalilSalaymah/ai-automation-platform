# Agent Scheduler & Background Task Queue - Implementation Summary

## Overview

A comprehensive scheduling and background task queue system has been added to the AI automation platform. The system provides Redis-backed task processing, YAML-based task definitions, event bus communication, and full status tracking.

## Components Implemented

### 1. Core Package (`packages/core/core/`)

#### Models (`scheduler_models.py`)
- `ScheduledTask`: Database model for task definitions
- `TaskExecution`: Execution records with status tracking (queued, running, failed, success, cancelled)
- `EventMessage`: Event bus message model
- Request/Response models for API

#### Task Queue (`task_queue.py`)
- Redis Queue (RQ) integration
- Task enqueueing with metadata
- Status tracking and updates
- Job cancellation
- Result retrieval

#### Scheduler (`scheduler.py`)
- YAML task definition loader
- Cron and interval-based scheduling
- Task registration and unregistration
- Integration with RQ Scheduler

#### Event Bus (`event_bus.py`)
- Redis pub/sub for inter-app communication
- Publish events (broadcast or targeted)
- Subscribe to events with callbacks
- Non-blocking event listening

#### Router (`scheduler_router.py`)
- REST API endpoints for task management
- Task CRUD operations
- Execution tracking endpoints
- Task enable/disable

#### Worker (`worker.py`)
- RQ worker for processing background tasks
- Queue-based task execution

### 2. App Integration

All apps in `/apps` have been integrated:

- ✅ `aiops-bot`
- ✅ `email-agent`
- ✅ `rag-chat`
- ✅ `scraper-agent`
- ✅ `support-bot`

Each app now:
- Includes the scheduler router at `/api/scheduler`
- Loads tasks from `tasks.yaml` on startup
- Can enqueue tasks programmatically
- Can publish/subscribe to events

### 3. Example Task Definitions

YAML task definition files created for each app:

- `apps/aiops-bot/tasks.yaml`
- `apps/email-agent/tasks.yaml`
- `apps/rag-chat/tasks.yaml`
- `apps/scraper-agent/tasks.yaml`
- `apps/support-bot/tasks.yaml`

### 4. Example Task Functions

Example scheduled task functions added to:
- `apps/email-agent/app/services/email_service.py`
- `apps/aiops-bot/app/services/aiops_service.py`

These demonstrate the pattern for creating schedulable tasks.

## Dependencies Added

Updated `packages/core/pyproject.toml`:
- `rq = "^1.15.0"` - Redis Queue
- `rq-scheduler = "^0.12.0"` - Scheduling support
- `pyyaml = "^6.0.1"` - YAML parsing
- `croniter = "^2.0.1"` - Cron validation

## Features

### ✅ Redis-backed RQ Task Queue
- Background job processing
- Job status tracking
- Result storage
- Error handling

### ✅ YAML Task Definitions
- Per-agent task configuration
- Cron and interval scheduling
- Function path specification
- Arguments and keyword arguments

### ✅ Event Bus
- Inter-app communication
- Broadcast and targeted events
- Callback-based subscriptions
- Non-blocking event listening

### ✅ Status Tracking
- Real-time task status (queued, running, failed, success, cancelled)
- Execution history
- Error tracking
- Result storage

### ✅ API Endpoints
- Task management (CRUD)
- Execution tracking
- Task enable/disable
- Execution cancellation

## Usage

### Starting a Worker

```bash
# Using the core worker
python -m core.worker

# Or with RQ directly
rq worker --url redis://localhost:6379/0
```

### Running RQ Scheduler

For scheduled tasks, also run the RQ scheduler:

```bash
rq-scheduler --url redis://localhost:6379/0
```

### API Endpoints

All apps expose scheduler endpoints at `/api/scheduler`:
- `GET /api/scheduler/tasks` - List tasks
- `POST /api/scheduler/tasks` - Create task
- `GET /api/scheduler/executions` - List executions
- etc.

### Event Publishing

```python
from core import EventBus

event_bus = EventBus()
event_bus.publish(
    event_type="task.completed",
    source_agent="email-agent",
    payload={"task_id": "123"}
)
```

## Database Tables

The system creates two new tables:
- `scheduled_tasks` - Task definitions
- `task_executions` - Execution records

These are automatically created via SQLModel on app startup.

## Next Steps

1. **Install Dependencies**: Run `poetry install` in `packages/core`
2. **Start Redis**: Ensure Redis is running
3. **Start Workers**: Run RQ workers for each app
4. **Start Scheduler**: Run RQ scheduler for scheduled tasks
5. **Configure Tasks**: Edit `tasks.yaml` files as needed
6. **Implement Task Functions**: Add actual task logic to service functions

## Documentation

See `packages/core/SCHEDULER_README.md` for detailed usage documentation.

