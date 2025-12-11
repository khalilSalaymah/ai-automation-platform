# Observability Implementation

This document describes the full observability features added to the AI Automation Platform.

## Features

### 1. Central Structured Logging (JSON)

All logs are now output in structured JSON format with the following fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, ERROR, WARNING, DEBUG)
- `message`: Log message
- `module`: Python module name
- `function`: Function name
- `line`: Line number
- `trace_id`: Request trace ID (for correlation)
- `span_id`: Operation span ID
- `parent_span_id`: Parent span ID (for nested operations)
- Additional metadata fields as needed

**Configuration:**
- Logs are written to:
  - `logs/app.log` - All logs (INFO and above)
  - `logs/error.log` - Error logs only
- Log rotation: 100MB for app.log, 10MB for error.log
- Retention: 30 days for app.log, 90 days for error.log

### 2. Request Tracing (trace_id)

Every HTTP request automatically gets a `trace_id` that:
- Is generated if not present in the `X-Trace-ID` header
- Is propagated through all services via headers
- Is included in all log entries for that request
- Can be used to trace a request across the entire system

**Usage:**
```python
from core.logger import get_trace_id, set_trace_id, generate_trace_id

# Get current trace_id
trace_id = get_trace_id()

# Set trace_id (usually done by middleware)
set_trace_id(trace_id)

# Generate new trace_id
new_trace_id = generate_trace_id()
```

### 3. Span Tracking

Operations are tracked as "spans" with:
- **LLM Calls**: Tracks OpenAI API calls with duration, model, and metadata
- **Tool Executions**: Tracks tool executions with duration and results
- **HTTP Requests**: Tracks request/response cycles

**Span Information:**
- `operation`: Type of operation (llm_call, tool_execution, http_request)
- `service`: Service name (openai, tool_registry, gateway)
- `duration_ms`: Duration in milliseconds
- `metadata`: Additional operation-specific metadata
- `error`: Error message if operation failed

**Usage:**
```python
from core.logger import log_span, generate_span_id, set_span_id, get_span_id
import time

start_time = time.time()
span_id = generate_span_id()
parent_span_id = get_span_id()  # Get current span as parent
set_span_id(span_id, parent_span_id)

try:
    # Your operation here
    result = perform_operation()
    end_time = time.time()
    
    log_span(
        operation="my_operation",
        service="my_service",
        metadata={"key": "value"},
        start_time=start_time,
        end_time=end_time,
    )
except Exception as e:
    end_time = time.time()
    log_span(
        operation="my_operation",
        service="my_service",
        start_time=start_time,
        end_time=end_time,
        error=str(e),
    )
```

### 4. Error Alerts to Slack

Errors are automatically sent to Slack via webhook when:
- An error occurs in LLM calls
- A tool execution fails
- An HTTP request fails
- Any unhandled exception occurs

**Configuration:**

Add to your `.env` file:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ENABLE_SLACK_ALERTS=true
```

**Alert Format:**
- Color-coded by severity (red for errors, orange for warnings)
- Includes trace_id and span_id for correlation
- Includes error message and metadata
- Includes stack trace for exceptions

**Usage:**
```python
from core.observability import log_error_with_alert

try:
    # Your code
    pass
except Exception as e:
    log_error_with_alert(
        message="Operation failed",
        error=e,
        metadata={"key": "value"},
        send_alert=True,  # Set to False to skip Slack alert
    )
```

### 5. Log Viewer Admin Page

A full-featured log viewer is available in the admin UI at `/admin/logs` (or wherever you mount the LogViewer component).

**Features:**
- **Filtering**: Filter by trace_id, span_id, level, operation, service
- **Source Selection**: View logs from database, files, or both
- **Trace View**: Click on a trace_id to see all logs for that trace
- **Statistics**: View log statistics (total, errors, warnings, by operation/service)
- **Error Details**: Expand error entries to see full stack traces
- **Real-time**: Refresh to get latest logs

**API Endpoints:**

- `GET /api/admin/logs` - Get logs with filtering
  - Query parameters:
    - `trace_id`: Filter by trace ID
    - `span_id`: Filter by span ID
    - `level`: Filter by log level
    - `operation`: Filter by operation type
    - `service`: Filter by service name
    - `start_time`: Filter logs after this time (ISO 8601)
    - `end_time`: Filter logs before this time (ISO 8601)
    - `limit`: Maximum number of entries (1-1000, default: 100)
    - `offset`: Number of entries to skip (default: 0)
    - `source`: Source to read from (`database`, `file`, or `both`, default: `both`)

- `GET /api/admin/logs/trace/{trace_id}` - Get all logs for a specific trace
  - Query parameters:
    - `limit`: Maximum number of entries (default: 1000)

- `GET /api/admin/logs/stats` - Get log statistics
  - Returns:
    - `total`: Total number of logs
    - `by_level`: Count by log level
    - `by_operation`: Count by operation type
    - `by_service`: Count by service
    - `error_count`: Total error count
    - `warning_count`: Total warning count

**UI Component Usage:**
```jsx
import { LogViewer } from '@ui/components';

function AdminPage() {
  return (
    <AdminLayout>
      <LogViewer apiUrl="http://localhost:8080" />
    </AdminLayout>
  );
}
```

## Database Models

Log entries can be stored in the database for efficient querying. The `LogEntry` model includes:
- All standard log fields
- Indexed fields: trace_id, span_id, timestamp, level, service
- JSON metadata field for flexible additional data
- Error information (type, value, traceback)

To enable database logging, you'll need to:
1. Run database migrations to create the `log_entries` table
2. Optionally implement a log ingestion service to write logs to the database

## Configuration

All observability settings are in `packages/core/core/config.py`:

```python
class Settings(BaseSettings):
    # ... other settings ...
    
    # Observability
    slack_webhook_url: str = ""  # Slack webhook URL for error alerts
    enable_slack_alerts: bool = False  # Enable/disable Slack alerts
```

Set these in your `.env` file:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ENABLE_SLACK_ALERTS=true
```

## Best Practices

1. **Trace ID Propagation**: Always propagate trace_id in HTTP headers when making requests to other services
2. **Span Nesting**: Use parent_span_id to create nested spans for complex operations
3. **Metadata**: Include relevant metadata in spans (user_id, request_id, etc.)
4. **Error Handling**: Use `log_error_with_alert` for critical errors that need immediate attention
5. **Log Levels**: Use appropriate log levels:
   - ERROR: Errors that need attention
   - WARNING: Warnings that should be monitored
   - INFO: Normal operations and spans
   - DEBUG: Detailed debugging information

## Example: Tracing a Request

Here's how a request flows through the system:

1. **Request arrives** → Middleware generates `trace_id`
2. **Request logged** → Log entry includes `trace_id`
3. **LLM call made** → New `span_id` created, parent is request span
4. **LLM span logged** → Includes `trace_id` and `parent_span_id`
5. **Tool executed** → New `span_id` created, parent is LLM span
6. **Tool span logged** → Includes `trace_id` and `parent_span_id`
7. **Response sent** → All logs can be correlated by `trace_id`

You can then:
- Filter logs by `trace_id` to see the entire request flow
- View spans to understand operation durations
- Identify bottlenecks by analyzing span durations
- Debug issues by following the trace

## Troubleshooting

**Logs not appearing:**
- Check that the `logs/` directory exists and is writable
- Verify log level configuration

**Slack alerts not working:**
- Verify `SLACK_WEBHOOK_URL` is set correctly
- Check `ENABLE_SLACK_ALERTS=true`
- Test webhook URL manually with curl

**Trace IDs not propagating:**
- Ensure middleware is added before other middleware
- Check that `X-Trace-ID` header is being forwarded in requests

**Log viewer not loading:**
- Verify admin authentication is working
- Check API endpoint is accessible
- Ensure database is initialized (if using database source)
