# Agent Scheduler & Background Task Queue

This package provides a comprehensive scheduling and task queue system for the AI automation platform.

## Features

- **Redis-backed RQ Task Queue**: Background job processing using Redis Queue (RQ)
- **YAML Task Definitions**: Define scheduled tasks in YAML files per agent
- **Event Bus**: Inter-app communication using Redis pub/sub
- **Status Tracking**: Track task status (queued, running, failed, success)
- **Cron & Interval Scheduling**: Support for both cron expressions and interval-based tasks

## Components

### 1. Task Queue (`task_queue.py`)
Manages background task execution using RQ:
- Enqueue tasks for immediate execution
- Track task status and results
- Cancel running tasks

### 2. Scheduler (`scheduler.py`)
Manages scheduled/recurring tasks:
- Load tasks from YAML files
- Register and unregister scheduled tasks
- Support for cron and interval-based scheduling

### 3. Event Bus (`event_bus.py`)
Enables inter-app communication:
- Publish events to specific agents or broadcast
- Subscribe to events with callbacks
- Listen for events (blocking or non-blocking)

### 4. Models (`scheduler_models.py`)
Database models for:
- `ScheduledTask`: Task definitions
- `TaskExecution`: Execution records with status tracking
- `EventMessage`: Event bus messages

## Usage

### 1. Define Tasks in YAML

Create a `tasks.yaml` file in your app directory:

```yaml
tasks:
  - name: process_pending_emails
    description: Process pending emails every 5 minutes
    enabled: true
    type: interval
    schedule: "5 minutes"
    function: "app.services.email_service:process_pending_emails_task"
    kwargs:
      batch_size: 10

  - name: daily_report
    description: Generate daily report at 9 AM
    enabled: true
    type: cron
    schedule: "0 9 * * *"
    function: "app.services.report_service:generate_report_task"
```

### 2. Create Task Functions

Task functions must be **synchronous** (not async) and importable:

```python
# app/services/email_service.py

def process_pending_emails_task(batch_size: int = 10) -> dict:
    """Scheduled task function."""
    from core.logger import logger
    from core.event_bus import EventBus
    
    logger.info(f"Processing {batch_size} pending emails")
    # Your task logic here
    
    # Optionally publish events
    event_bus = EventBus()
    event_bus.publish(
        event_type="email.batch_processed",
        source_agent="email-agent",
        payload={"batch_size": batch_size}
    )
    
    return {"status": "success", "processed": batch_size}
```

### 3. Integrate into App

The scheduler is automatically initialized on app startup if a `tasks.yaml` file exists:

```python
# app/main.py
from core import scheduler_router, TaskScheduler
from pathlib import Path

app.include_router(scheduler_router, prefix="/api/scheduler", tags=["scheduler"])

@app.on_event("startup")
async def startup():
    init_db()
    
    # Load and register tasks from YAML
    scheduler = TaskScheduler()
    yaml_path = Path(__file__).parent.parent / "tasks.yaml"
    if yaml_path.exists():
        tasks = scheduler.load_tasks_from_yaml(str(yaml_path), agent_name="your-agent")
        for task in tasks:
            scheduler.register_task(task)
```

### 4. Run RQ Worker

Start a worker to process tasks:

```bash
# Using the core worker
python -m core.worker

# Or with a specific queue
python -m core.worker my_queue
```

Or use RQ directly:

```bash
rq worker --url redis://localhost:6379/0
```

### 5. Enqueue Tasks Programmatically

```python
from core import TaskQueue

task_queue = TaskQueue()
job_id = task_queue.enqueue(
    func=my_function,
    agent_name="my-agent",
    task_name="my-task",
    function_path="app.services:my_function",
    args=(arg1, arg2),
    kwargs={"key": "value"}
)
```

### 6. Use Event Bus

```python
from core import EventBus

# Publish an event
event_bus = EventBus()
event_bus.publish(
    event_type="task.completed",
    source_agent="email-agent",
    payload={"task_id": "123", "status": "success"}
)

# Subscribe to events
def handle_event(event: EventMessage):
    print(f"Received {event.event_type} from {event.source_agent}")

event_bus.subscribe(
    agent_name="support-bot",
    event_type="task.completed",
    callback=handle_event
)

# Listen for events (in a loop)
while True:
    event = event_bus.listen(timeout=1.0)
    if event:
        print(f"Event: {event.event_type}")
```

## API Endpoints

The scheduler router provides REST API endpoints:

- `POST /api/scheduler/tasks` - Create a scheduled task
- `GET /api/scheduler/tasks` - List all tasks (optionally filter by agent)
- `GET /api/scheduler/tasks/{task_id}` - Get a specific task
- `DELETE /api/scheduler/tasks/{task_id}` - Delete a task
- `POST /api/scheduler/tasks/{task_id}/enable` - Enable a task
- `POST /api/scheduler/tasks/{task_id}/disable` - Disable a task
- `GET /api/scheduler/executions` - List task executions
- `GET /api/scheduler/executions/{execution_id}` - Get execution details
- `POST /api/scheduler/executions/{execution_id}/cancel` - Cancel an execution

## Schedule Formats

### Cron Expression
Standard cron format: `minute hour day month weekday`

Examples:
- `0 9 * * *` - Every day at 9 AM
- `0 */2 * * *` - Every 2 hours
- `0 0 * * 1` - Every Monday at midnight

### Interval
Human-readable intervals: `{number} {unit}`

Examples:
- `5 minutes`
- `1 hour`
- `30 seconds`
- `2 days`
- `1 week`

## Task Status

Tasks can have the following statuses:
- `queued` - Task is in the queue waiting to be processed
- `running` - Task is currently executing
- `success` - Task completed successfully
- `failed` - Task failed with an error
- `cancelled` - Task was cancelled

## Event Types

Common event type patterns:
- `{agent}.{action}` - e.g., `email.processed`, `aiops.alert_triggered`
- `task.{status}` - e.g., `task.completed`, `task.failed`
- `system.{event}` - e.g., `system.startup`, `system.shutdown`

## Configuration

Ensure Redis is configured in your environment:

```env
REDIS_URL=redis://localhost:6379/0
```

## Dependencies

- `rq` - Redis Queue for task processing
- `rq-scheduler` - Scheduling support for RQ
- `pyyaml` - YAML parsing
- `croniter` - Cron expression validation
- `redis` - Redis client

## Best Practices

1. **Task Functions**: Keep task functions idempotent when possible
2. **Error Handling**: Always handle errors gracefully in task functions
3. **Logging**: Use the core logger for consistent logging
4. **Events**: Publish events for important state changes
5. **Resource Management**: Clean up resources in task functions
6. **Testing**: Test task functions independently before scheduling

## Example: Complete Workflow

1. Define task in `tasks.yaml`
2. Create task function in service
3. App loads tasks on startup
4. RQ worker processes tasks
5. Task publishes event on completion
6. Other apps subscribe and react to events

This creates a decoupled, event-driven architecture where apps can communicate and coordinate through the event bus.

