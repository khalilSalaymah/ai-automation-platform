# Agent Marketplace

A comprehensive marketplace system for deploying and managing AI agents across organizations.

## Features

- **Agent Catalog**: Browse and discover available agents
- **JSON Config Schema**: Define agent configuration using JSON Schema
- **Per-Organization Deployment**: Deploy agents with organization-specific configurations
- **Enable/Disable**: Control agent availability per organization
- **Configuration Management**: Update agent configurations after deployment
- **Automatic Task Setup**: Background tasks are automatically configured on deployment
- **Tool Permissions**: Track required tools for each agent

## Architecture

### Database Models

#### Agent
Stores agent definitions in the marketplace:
- `id`: Unique identifier
- `name`: Agent identifier (e.g., "email-agent")
- `display_name`: Human-readable name
- `description`: Agent description
- `config_schema`: JSON Schema for configuration
- `required_tools`: List of required tool names
- `default_tasks`: Default scheduled tasks configuration
- `category`, `tags`, `version`, etc.

#### OrganizationAgent
Tracks agent deployments per organization:
- `org_id`: Organization ID
- `agent_id`: Reference to Agent
- `status`: Deployment status (available, deployed, disabled, error)
- `config`: Organization-specific configuration
- `deployed_at`, `deployed_by`: Deployment metadata
- `last_error`, `error_at`: Error tracking

### API Endpoints

All endpoints are prefixed with `/api/marketplace`:

- `GET /agents` - List all available agents
- `GET /agents/{agent_id}` - Get agent details
- `GET /organization/agents` - List deployed agents for organization
- `GET /organization/agents/{agent_id}` - Get organization agent deployment
- `POST /organization/agents/{agent_id}/deploy` - Deploy an agent
- `PUT /organization/agents/{agent_id}/config` - Update agent configuration
- `POST /organization/agents/{agent_id}/enable` - Enable an agent
- `POST /organization/agents/{agent_id}/disable` - Disable an agent

### Configuration Schema

Agents define their configuration using JSON Schema format:

```json
{
  "type": "object",
  "properties": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Service API key",
      "format": "password"
    },
    "check_interval": {
      "type": "integer",
      "title": "Check Interval (minutes)",
      "default": 5,
      "minimum": 1,
      "maximum": 60
    },
    "auto_reply": {
      "type": "boolean",
      "title": "Enable Auto-Reply",
      "default": false
    }
  },
  "required": ["api_key"]
}
```

The UI automatically generates forms based on this schema with:
- Field type detection (string, number, boolean, array, object)
- Required field validation
- Format validation (email, URI, password)
- Min/max constraints
- Enum support for dropdowns
- Default values

### Scheduled Tasks

When an agent is deployed, its `default_tasks` are automatically set up:

```json
{
  "tasks": [
    {
      "name": "process_emails",
      "description": "Process emails every 5 minutes",
      "enabled": true,
      "type": "interval",
      "schedule": "5 minutes",
      "function": "app.services.email_service:process_task",
      "kwargs": {
        "batch_size": 10
      }
    }
  ]
}
```

Tasks are created with organization-specific IDs: `{org_id}:{agent_name}:{task_name}`

### Tool Permissions

Agents declare required tools in `required_tools`. When deployed:
- Tool permissions are logged
- Tools should be registered in the ToolRegistry
- Runtime access is controlled by the agent execution context

## Usage

### Seeding the Marketplace

Populate the marketplace with example agents:

```python
from core.agent_marketplace_seed import seed_agents
from core.database import engine
from sqlmodel import Session

with Session(engine) as session:
    seed_agents(session)
```

### Deploying an Agent

1. Browse available agents in the UI
2. Click "Deploy" on an agent
3. Fill in the configuration form (generated from JSON Schema)
4. Click "Deploy Agent"
5. Background tasks are automatically set up
6. Agent status changes to "deployed"

### Updating Configuration

1. Find the deployed agent in the marketplace
2. Click "Configure"
3. Update configuration values
4. Click "Update Configuration"
5. Tasks are updated with new configuration

### Enabling/Disabling

- **Enable**: Activates the agent and enables all scheduled tasks
- **Disable**: Deactivates the agent and disables all scheduled tasks

## UI Components

### AgentMarketplace
Main component for browsing and managing agents:
- Agent grid with cards
- Search and category filtering
- Status indicators
- Deploy/Configure/Enable/Disable actions

### AgentConfigForm
Modal form for agent configuration:
- Auto-generated from JSON Schema
- Field validation
- Support for all JSON Schema types
- Password field masking
- Array and object editing

## Integration

The marketplace router is included in the gateway service:

```python
from core.agent_marketplace_router import router as agent_marketplace_router

app.include_router(
    agent_marketplace_router,
    prefix="/api/marketplace",
    tags=["marketplace"]
)
```

## Example Agent Definition

```python
{
    "name": "email-agent",
    "display_name": "Email Automation Agent",
    "description": "Automate email processing and responses",
    "version": "1.0.0",
    "category": "automation",
    "config_schema": {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "title": "API Key",
                "format": "password"
            },
            "email_address": {
                "type": "string",
                "title": "Email Address",
                "format": "email"
            }
        },
        "required": ["api_key", "email_address"]
    },
    "required_tools": ["send_email", "read_email"],
    "default_tasks": {
        "tasks": [
            {
                "name": "process_emails",
                "type": "interval",
                "schedule": "5 minutes",
                "function": "app.services.email_service:process_task"
            }
        ]
    },
    "tags": ["email", "automation"]
}
```

## Security

- All endpoints require authentication
- Organization isolation via `org_id`
- Configuration values are stored securely
- Password fields are masked in the UI
- API keys and secrets are stored as-is (consider encryption for production)

## Future Enhancements

- Tool permission management UI
- Agent versioning and updates
- Deployment history and rollback
- Agent analytics and usage tracking
- Custom agent creation UI
- Agent templates and marketplace sharing
