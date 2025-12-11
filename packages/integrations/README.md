# Integrations Package

This package provides plug-and-play integration connectors for external services. Each connector implements OAuth authentication, secure token storage, and exposes agent tools for use with the AI automation platform.

## Supported Integrations

- **Slack** - Team communication and messaging
- **Gmail** - Email management (OAuth)
- **Outlook** - Microsoft 365 email (OAuth)
- **Notion** - Workspace and knowledge management
- **Stripe** - Payment processing (API key based)
- **Airtable** - Database and workflow management
- **Shopify** - E-commerce platform
- **Google Calendar** - Calendar and event management

## Features

- ✅ OAuth 2.0 authentication flow
- ✅ Encrypted token storage using Fernet encryption
- ✅ Automatic token refresh (where supported)
- ✅ Plug-and-play agent tools via ToolRegistry
- ✅ Standardized connector interface

## Installation

```bash
cd packages/integrations
poetry install
```

## Configuration

Add the following environment variables to your `.env` file:

```env
# Encryption key for token storage (REQUIRED)
INTEGRATION_ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# Google (for Gmail and Google Calendar)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft/Outlook
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Slack
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Notion
NOTION_CLIENT_ID=your-notion-client-id
NOTION_CLIENT_SECRET=your-notion-client-secret

# Airtable
AIRTABLE_CLIENT_ID=your-airtable-client-id
AIRTABLE_CLIENT_SECRET=your-airtable-client-secret

# Shopify
SHOPIFY_CLIENT_ID=your-shopify-client-id
SHOPIFY_CLIENT_SECRET=your-shopify-client-secret
SHOPIFY_SHOP_NAME=your-shop-name

# Stripe (API key, not OAuth)
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Generating Encryption Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this as INTEGRATION_ENCRYPTION_KEY
```

## Usage

### Basic Usage

```python
from integrations import SlackConnector, ToolRegistry

# Initialize connector for a user
connector = SlackConnector(user_id="user-123", org_id="org-456")

# Get OAuth URL
oauth_url = connector.get_oauth_url(
    redirect_uri="https://yourapp.com/oauth/callback",
    state="csrf-protection-token"
)

# After user authorizes, handle callback
token_data = await connector.handle_oauth_callback(
    code="authorization-code",
    redirect_uri="https://yourapp.com/oauth/callback"
)

# Register tools with agent
registry = ToolRegistry()
connector.register_tools(registry)

# Use tools
result = registry.execute("slack_send_message", {
    "channel": "#general",
    "text": "Hello from AI agent!"
})
```

### OAuth Flow Example

```python
from fastapi import FastAPI, Request
from integrations import GmailConnector

app = FastAPI()

@app.get("/oauth/gmail/authorize")
async def authorize_gmail(request: Request):
    connector = GmailConnector(user_id=request.state.user_id)
    redirect_uri = f"{request.base_url}oauth/gmail/callback"
    oauth_url = connector.get_oauth_url(redirect_uri=redirect_uri)
    return {"oauth_url": oauth_url}

@app.get("/oauth/gmail/callback")
async def gmail_callback(code: str, state: str, request: Request):
    connector = GmailConnector(user_id=request.state.user_id)
    redirect_uri = f"{request.base_url}oauth/gmail/callback"
    token_data = await connector.handle_oauth_callback(
        code=code,
        redirect_uri=redirect_uri
    )
    return {"status": "success", "token_data": token_data}
```

### Using with Agents

```python
from core.agents import ToolExecutionAgent
from core.llm import LLM
from integrations import SlackConnector, GmailConnector, ToolRegistry

# Initialize LLM
llm = LLM()

# Create tool registry
registry = ToolRegistry()

# Register integration tools
slack = SlackConnector(user_id="user-123")
slack.load_tokens()  # Load existing tokens
slack.register_tools(registry)

gmail = GmailConnector(user_id="user-123")
gmail.load_tokens()
gmail.register_tools(registry)

# Create agent with tools
agent = ToolExecutionAgent(
    name="assistant",
    llm=llm,
    tools=registry
)

# Agent can now use integration tools
response = agent.act({
    "query": "Send a Slack message to #general saying 'Meeting at 3pm'",
    "session_id": "session-123"
})
```

## Available Tools

### Slack
- `slack_send_message` - Send message to channel
- `slack_list_channels` - List all channels
- `slack_get_channel_history` - Get channel message history
- `slack_get_user_info` - Get user information

### Gmail
- `gmail_list_messages` - List emails from inbox
- `gmail_get_message` - Get specific email
- `gmail_send_message` - Send email
- `gmail_mark_read` - Mark email as read

### Outlook
- `outlook_list_messages` - List emails
- `outlook_get_message` - Get specific email
- `outlook_send_message` - Send email
- `outlook_mark_read` - Mark email as read

### Notion
- `notion_search_pages` - Search for pages
- `notion_get_page` - Get page by ID
- `notion_create_page` - Create new page
- `notion_update_page` - Update page
- `notion_get_databases` - List databases

### Stripe
- `stripe_list_customers` - List customers
- `stripe_get_customer` - Get customer by ID
- `stripe_create_customer` - Create customer
- `stripe_list_subscriptions` - List subscriptions
- `stripe_get_invoice` - Get invoice by ID

### Airtable
- `airtable_list_bases` - List all bases
- `airtable_list_tables` - List tables in base
- `airtable_list_records` - List records from table
- `airtable_get_record` - Get specific record
- `airtable_create_record` - Create record
- `airtable_update_record` - Update record

### Shopify
- `shopify_list_products` - List products
- `shopify_get_product` - Get product by ID
- `shopify_create_product` - Create product
- `shopify_list_orders` - List orders
- `shopify_get_order` - Get order by ID
- `shopify_list_customers` - List customers

### Google Calendar
- `calendar_list_calendars` - List all calendars
- `calendar_list_events` - List events
- `calendar_get_event` - Get event by ID
- `calendar_create_event` - Create event
- `calendar_update_event` - Update event
- `calendar_delete_event` - Delete event

## Token Management

Tokens are automatically encrypted and stored in the database using the `IntegrationToken` model. The encryption uses Fernet symmetric encryption with a key from the `INTEGRATION_ENCRYPTION_KEY` environment variable.

### Manual Token Management

```python
# Store tokens manually
connector.store_tokens(
    token="access-token",
    refresh_token="refresh-token",
    expires_at=datetime.utcnow() + timedelta(hours=1)
)

# Load tokens
connector.load_tokens()

# Check authentication
if connector.is_authenticated():
    print("User is authenticated")

# Refresh token (if supported)
if connector.refresh_access_token():
    print("Token refreshed successfully")
```

## Architecture

### BaseConnector

All connectors inherit from `BaseConnector` which provides:
- Token storage and retrieval
- OAuth URL generation (abstract)
- OAuth callback handling (abstract)
- Tool registration interface (abstract)

### IntegrationToken Model

Stores encrypted OAuth tokens with:
- User and organization scoping
- Token expiration tracking
- Metadata storage (JSON)
- Automatic encryption/decryption

## Security

- All tokens are encrypted at rest using Fernet encryption
- Encryption key should be stored securely (not in code)
- Tokens are scoped to users and organizations
- OAuth state parameter for CSRF protection
- Automatic token refresh where supported

## Development

### Adding a New Integration

1. Create a new file in `integrations/` directory
2. Inherit from `BaseConnector`
3. Implement required abstract methods:
   - `get_oauth_url()`
   - `handle_oauth_callback()`
   - `get_tools()`
   - `register_tools()`
4. Add OAuth credentials to `core/config.py`
5. Export in `integrations/__init__.py`

Example:

```python
from .base import BaseConnector
from core.tools import ToolRegistry

class MyServiceConnector(BaseConnector):
    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("my_service", user_id, org_id)
    
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        # Implement OAuth URL generation
        pass
    
    async def handle_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        # Implement token exchange
        pass
    
    def get_tools(self) -> List[Dict[str, Any]]:
        # Return tool definitions
        pass
    
    def register_tools(self, registry: ToolRegistry):
        # Register tools with registry
        pass
```

## Testing

```bash
pytest tests/
```

## License

See main project LICENSE file.
