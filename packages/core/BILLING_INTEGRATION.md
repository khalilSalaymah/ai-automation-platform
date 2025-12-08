# Stripe Billing Integration Guide

This guide explains how to integrate Stripe subscriptions and usage metering into your applications.

## Setup

### 1. Install Dependencies

The Stripe dependency is already included in `packages/core/pyproject.toml`. Install it:

```bash
cd packages/core
poetry install
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (create these in Stripe Dashboard)
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### 3. Create Stripe Products and Prices

1. Go to Stripe Dashboard → Products
2. Create three products: Basic, Pro, Enterprise
3. Create prices for each product (monthly subscription)
4. Copy the Price IDs and add them to your `.env` file

### 4. Set Up Webhook Endpoint

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-domain.com/api/billing/webhook`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`

## Integration

### Backend Integration

#### 1. Include Billing Router

In your FastAPI app's `main.py`:

```python
from core import auth_router, billing_router, init_db

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include billing router
app.include_router(billing_router, prefix="/api")
```

#### 2. Record Usage

Use the usage metering utilities to track usage:

```python
from core.usage_meter import (
    record_token_usage,
    record_api_call_usage,
    record_scraping_task_usage,
    check_token_quota,
    check_api_call_quota,
    check_scraping_task_quota,
)
from core.database import get_session

# In your endpoint
@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    # Check quota before processing
    allowed, error = check_token_quota(session, current_user.id, requested_tokens=1000)
    if not allowed:
        raise HTTPException(status_code=403, detail=error)
    
    # Process request...
    tokens_used = 500
    
    # Record usage
    record_token_usage(
        session=session,
        user_id=current_user.id,
        tokens=tokens_used,
        metadata={"model": "gpt-4", "endpoint": "/api/chat"}
    )
    
    return {"response": "..."}
```

#### 3. Example: Scraper Agent

```python
@app.post("/api/scraper/scrape")
async def scrape(
    url: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    # Check quota
    allowed, error = check_scraping_task_quota(session, current_user.id)
    if not allowed:
        raise HTTPException(status_code=403, detail=error)
    
    # Perform scraping...
    result = scrape_url(url)
    
    # Record usage
    record_scraping_task_usage(
        session=session,
        user_id=current_user.id,
        metadata={"url": url, "pages": len(result)}
    )
    
    return result
```

### Frontend Integration

#### 1. Add Billing Dashboard Route

In your React app's router:

```jsx
import { BillingDashboard } from '@ui/components/BillingDashboard';
import { BillingAdmin } from '@ui/components/BillingAdmin';
import { AdminGuard } from '@ui/components/AuthGuard';

// Client billing dashboard
<Route path="/billing" element={
  <AuthGuard>
    <BillingDashboard apiUrl="http://localhost:8000" />
  </AuthGuard>
} />

// Admin billing dashboard
<Route path="/admin/billing" element={
  <AdminGuard>
    <BillingAdmin apiUrl="http://localhost:8000" />
  </AdminGuard>
} />
```

#### 2. Usage in Components

The billing components handle all Stripe interactions:
- Creating checkout sessions
- Opening customer portal
- Displaying usage and invoices
- Managing subscriptions

## Database Models

The billing system creates the following tables:
- `subscriptions` - User subscriptions
- `quotas` - Quota limits per subscription
- `usage` - Usage tracking records
- `invoices` - Invoice records

Run `init_db()` on startup to create these tables.

## API Endpoints

### Client Endpoints

- `POST /api/billing/checkout` - Create checkout session
- `POST /api/billing/portal` - Create customer portal session
- `GET /api/billing/subscription` - Get current subscription
- `GET /api/billing/quota` - Get quota limits
- `GET /api/billing/usage` - Get usage summary
- `GET /api/billing/invoices` - Get invoices

### Admin Endpoints

- `GET /api/billing/admin/users` - Get all users with usage
- `GET /api/billing/admin/invoices` - Get all invoices

### Webhook

- `POST /api/billing/webhook` - Stripe webhook handler

## Usage Metering

The system tracks three types of usage:
1. **Tokens** - LLM token usage
2. **API Calls** - API endpoint calls
3. **Scraping Tasks** - Web scraping operations

Usage is tracked monthly and resets at the start of each month.

## Quota Limits

Default quota limits (can be customized in `BillingService.get_quota_limits_for_price`):

- **Basic**: 100K tokens, 1K API calls, 100 scraping tasks
- **Pro**: 1M tokens, 10K API calls, 1K scraping tasks
- **Enterprise**: Unlimited (0 = unlimited)

## Testing

### Test Mode

Use Stripe test mode keys for development:
- Test API keys start with `sk_test_` and `pk_test_`
- Use test card: `4242 4242 4242 4242`
- Use Stripe CLI to forward webhooks: `stripe listen --forward-to localhost:8000/api/billing/webhook`

### Webhook Testing

Use Stripe CLI to test webhooks locally:

```bash
stripe listen --forward-to localhost:8000/api/billing/webhook
```

This will provide a webhook secret that you can use for local testing.
