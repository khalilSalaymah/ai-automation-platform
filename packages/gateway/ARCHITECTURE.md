# Gateway Architecture

## Overview

The Gateway service acts as a reverse proxy and API gateway for the AI Automation Platform. It handles authentication, rate limiting, quota checking, and request routing to agent services.

## Components

### 1. Main Application (`app/main.py`)

- FastAPI application entry point
- Middleware configuration
- Router registration
- Startup/shutdown handlers

### 2. Configuration (`app/config.py`)

- Service settings
- Agent service URLs
- Rate limiting configuration
- Database configuration

### 3. Middleware

#### Authentication Middleware (`app/middleware/auth.py`)
- JWT token validation
- Token decoding and verification
- User authentication

#### Rate Limiting Middleware (`app/middleware/rate_limit.py`)
- Per-user rate limiting
- Configurable limits (per minute/hour)
- In-memory storage (use Redis in production)

#### Quota Middleware (`app/middleware/quota.py`)
- Billing quota checking
- Usage type determination based on agent
- Database integration for quota validation

#### Logging Middleware (`app/middleware/logging.py`)
- Request/response logging
- Performance metrics
- Error tracking

### 4. Routing Service (`app/services/routing.py`)

- Agent service discovery
- Request forwarding
- Response handling
- Error handling and timeout management

### 5. Gateway Router (`app/routers/gateway_router.py`)

- Catch-all route for agent requests
- Usage recording
- Response formatting

### 6. Python SDK (`sdk/`)

- Client library for external developers
- Agent-specific clients
- Error handling
- Type hints

## Request Flow

```
1. External Request
   ↓
2. Logging Middleware (logs request)
   ↓
3. Rate Limit Middleware (checks rate limits)
   ↓
4. Quota Middleware (checks billing quotas)
   ↓
5. Auth Middleware (validates JWT token)
   ↓
6. Gateway Router (routes to agent)
   ↓
7. Routing Service (forwards to agent service)
   ↓
8. Agent Service (processes request)
   ↓
9. Response flows back through middleware
   ↓
10. Logging Middleware (logs response)
```

## Agent Routing

The gateway routes requests based on URL patterns:

- `/api/email/*` → Email Agent Service
- `/api/rag/*` → RAG Agent Service
- `/api/scraper/*` → Scraper Agent Service
- `/api/support/*` → Support Agent Service
- `/api/aiops/*` → AIOps Agent Service

## Error Handling

The gateway handles various error scenarios:

- **401 Unauthorized**: Invalid or missing JWT token
- **402 Payment Required**: Quota exceeded
- **429 Too Many Requests**: Rate limit exceeded
- **502 Bad Gateway**: Agent service unavailable
- **504 Gateway Timeout**: Agent service timeout

## Security

- JWT token validation on all requests
- Rate limiting to prevent abuse
- Quota checking to enforce billing limits
- Request logging for audit trails

## Performance

- Async request handling
- Connection pooling for agent services
- Configurable timeouts
- Efficient middleware chain

## Scalability

- Stateless design (except rate limiting)
- Can be horizontally scaled
- Use Redis for distributed rate limiting in production
- Load balancer friendly

## Monitoring

- Request/response logging
- Performance metrics (response time)
- Error tracking
- User activity tracking
