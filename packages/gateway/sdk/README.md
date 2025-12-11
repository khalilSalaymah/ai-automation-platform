# Gateway Python SDK

Simple Python SDK for interacting with the AI Automation Platform Gateway.

## Installation

```bash
pip install gateway-sdk
```

Or install from source:

```bash
cd packages/gateway
pip install -e .
```

## Quick Start

```python
from gateway_sdk import GatewayClient

# Initialize client
client = GatewayClient(
    base_url="https://api.example.com",
    api_key="your-jwt-token"
)

# Use agent clients
response = client.email.process({
    "subject": "Hello",
    "body": "World"
})

print(response)
```

## Examples

### Email Agent

```python
from gateway_sdk import GatewayClient

client = GatewayClient(
    base_url="http://localhost:8080",
    api_key="your-token"
)

# Process email
result = client.email.process({
    "subject": "Test",
    "body": "Email content"
})

# Generate response
response = client.email.respond({
    "subject": "Re: Test",
    "body": "Original email content"
})

# Get history
history = client.email.get_history(limit=10, offset=0)
```

### RAG Agent

```python
# Chat with RAG
response = client.rag.chat("What is artificial intelligence?")

# Upload document
doc_id = client.rag.upload_document("/path/to/document.pdf")

# List documents
documents = client.rag.list_documents()
```

### Raw Requests

```python
# Make custom requests
response = client.request(
    "GET",
    "/api/email/history",
    params={"limit": 10}
)
```

### Error Handling

```python
from gateway_sdk import (
    GatewayClient,
    AuthenticationError,
    QuotaExceededError,
    RateLimitError
)

try:
    response = client.email.process({"subject": "Test"})
except AuthenticationError:
    print("Invalid API key")
except QuotaExceededError as e:
    print(f"Quota exceeded: {e}")
except RateLimitError:
    print("Rate limit exceeded")
except GatewayError as e:
    print(f"Gateway error: {e}")
```

## API Reference

### GatewayClient

Main client class for interacting with the gateway.

#### Methods

- `request(method, path, params=None, json=None, data=None)`: Make a raw request
- `close()`: Close the HTTP client

#### Agent Clients

- `client.email`: Email agent client
- `client.rag`: RAG agent client
- `client.scraper`: Scraper agent client
- `client.support`: Support agent client
- `client.aiops`: AIOps agent client

### AgentClient

Base client for agent-specific operations.

#### Methods

- `get(path, params=None)`: GET request
- `post(path, json=None, data=None)`: POST request
- `put(path, json=None, data=None)`: PUT request
- `patch(path, json=None, data=None)`: PATCH request
- `delete(path)`: DELETE request

## Context Manager

The client can be used as a context manager:

```python
with GatewayClient(base_url="...", api_key="...") as client:
    response = client.email.process({"subject": "Test"})
```
