# Gateway Service

API Gateway service for the AI Automation Platform. Routes external requests to agent services with authentication, rate limiting, quota checking, and logging.

## Features

- **JWT Authentication**: Validates JWT tokens for all requests
- **Rate Limiting**: Per-user rate limiting (configurable per minute/hour)
- **Billing Quota Checking**: Validates user quotas before routing requests
- **Request Logging**: Logs every request with detailed information
- **Agent Routing**: Routes requests to appropriate agent services via internal HTTP
- **Python SDK**: Simple SDK for external developers

## Architecture

The gateway acts as a reverse proxy, forwarding requests to agent services:

```
External Request → Gateway → Agent Service
```

The gateway handles:
1. JWT validation
2. Rate limiting
3. Quota checking
4. Request logging
5. Request forwarding
6. Response handling

## Setup

1. Install dependencies:
```bash
cd packages/gateway
pip install -e .
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Configure agent service URLs in `.env`:
```env
EMAIL_AGENT_URL=http://localhost:8081
RAG_AGENT_URL=http://localhost:8082
SCRAPER_AGENT_URL=http://localhost:8083
SUPPORT_AGENT_URL=http://localhost:8084
AIOPS_AGENT_URL=http://localhost:8085
```

4. Run the gateway:
```bash
uvicorn app.main:app --reload --port 8080
```

## API Usage

### Authentication

All requests require a JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8080/api/email/process
```

### Routing

The gateway routes requests based on the path:

- `/api/email/*` → Email Agent
- `/api/rag/*` → RAG Agent
- `/api/scraper/*` → Scraper Agent
- `/api/support/*` → Support Agent
- `/api/aiops/*` → AIOps Agent

### Example Requests

**Email Agent:**
```bash
curl -X POST http://localhost:8080/api/email/process \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"subject": "Hello", "body": "World"}'
```

**RAG Agent:**
```bash
curl -X POST http://localhost:8080/api/rag/chat \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is AI?"}'
```

## Python SDK

The gateway includes a Python SDK for external developers:

### Installation

```bash
pip install gateway-sdk
```

### Usage

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

# RAG chat
response = client.rag.chat("What is AI?")

# Raw requests
response = client.request("GET", "/api/email/history", params={"limit": 10})
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
    response = client.email.process({"subject": "Hello"})
except AuthenticationError:
    print("Invalid API key")
except QuotaExceededError as e:
    print(f"Quota exceeded: {e}")
except RateLimitError:
    print("Rate limit exceeded")
except GatewayError as e:
    print(f"Gateway error: {e}")
```

## Configuration

### Rate Limiting

Configure rate limits in `.env`:

```env
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### Request Timeout

Configure request timeout:

```env
REQUEST_TIMEOUT=30
```

## Middleware

The gateway uses the following middleware (in order):

1. **Logging Middleware**: Logs all requests
2. **Rate Limit Middleware**: Enforces rate limits
3. **Quota Middleware**: Checks billing quotas
4. **Auth Middleware**: Validates JWT tokens (in routes)

## Development

Run with hot reload:

```bash
uvicorn app.main:app --reload --port 8080
```

Run tests:

```bash
pytest
```

## Production Considerations

1. **Rate Limiting**: Use Redis for distributed rate limiting in production
2. **Logging**: Consider using structured logging and log aggregation
3. **Monitoring**: Add metrics and health checks
4. **Security**: Configure CORS appropriately
5. **Load Balancing**: Use a load balancer for high availability

## Agent Service Requirements

Agent services should:
- Accept requests on the configured ports
- Handle the same HTTP methods as the gateway
- Return appropriate status codes
- Include proper error handling
