# Stripe Billing Integration

Complete Stripe subscription and usage metering integration for the AI Automation Platform monorepo.

## ✅ Implementation Complete

### Backend (packages/core)

1. **Billing Models** (`core/billing_models.py`)
   - `Subscription` - Tracks user subscriptions
   - `Quota` - Defines usage limits per subscription
   - `Usage` - Records usage (tokens, API calls, scraping tasks)
   - `Invoice` - Stores invoice records
   - Response models for API

2. **Billing Service** (`core/billing_service.py`)
   - Stripe checkout session creation
   - Customer portal session creation
   - Subscription synchronization from webhooks
   - Quota management based on subscription plans
   - Usage recording and tracking
   - Quota checking before operations
   - Usage summary generation

3. **Billing Router** (`core/billing_router.py`)
   - `POST /api/billing/checkout` - Create checkout session
   - `POST /api/billing/portal` - Open customer portal
   - `GET /api/billing/subscription` - Get current subscription
   - `GET /api/billing/quota` - Get quota limits
   - `GET /api/billing/usage` - Get usage summary
   - `GET /api/billing/invoices` - Get user invoices
   - `GET /api/billing/admin/users` - Admin: view all users & usage
   - `GET /api/billing/admin/invoices` - Admin: view all invoices
   - `POST /api/billing/webhook` - Stripe webhook handler

4. **Usage Metering** (`core/usage_meter.py`)
   - `record_token_usage()` - Record token consumption
   - `record_api_call_usage()` - Record API calls
   - `record_scraping_task_usage()` - Record scraping tasks
   - `check_token_quota()` - Check token quota before operation
   - `check_api_call_quota()` - Check API call quota
   - `check_scraping_task_quota()` - Check scraping task quota

5. **Configuration** (`core/config.py`)
   - Added Stripe configuration settings:
     - `stripe_secret_key`
     - `stripe_publishable_key`
     - `stripe_webhook_secret`
     - `stripe_price_basic`
     - `stripe_price_pro`
     - `stripe_price_enterprise`

### Frontend (packages/ui)

1. **BillingDashboard Component** (`components/BillingDashboard.jsx`)
   - View current subscription status
   - Display usage metrics with progress bars
   - View invoices
   - Upgrade to different plans
   - Manage subscription via Stripe portal
   - Real-time usage tracking

2. **BillingAdmin Component** (`components/BillingAdmin.jsx`)
   - View all users with subscription status
   - View usage metrics per user
   - View all invoices
   - Admin-only access

## 📋 Setup Instructions

### 1. Install Dependencies

```bash
cd packages/core
poetry install
```

### 2. Configure Stripe

1. Create a Stripe account at https://stripe.com
2. Get your API keys from Dashboard → Developers → API keys
3. Create three products with monthly prices:
   - Basic Plan
   - Pro Plan
   - Enterprise Plan
4. Copy the Price IDs

### 3. Set Environment Variables

Add to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### 4. Set Up Webhook

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-domain.com/api/billing/webhook`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. Copy webhook signing secret

### 5. Integrate into Your App

#### Backend

In your FastAPI `main.py`:

```python
from core import auth_router, billing_router, init_db

app.include_router(auth_router, prefix="/api")
app.include_router(billing_router, prefix="/api")
```

#### Frontend

In your React router:

```jsx
import { BillingDashboard, BillingAdmin } from '@ui/components';
import { AuthGuard, AdminGuard } from '@ui/components';

<Route path="/billing" element={
  <AuthGuard>
    <BillingDashboard apiUrl="http://localhost:8000" />
  </AuthGuard>
} />

<Route path="/admin/billing" element={
  <AdminGuard>
    <BillingAdmin apiUrl="http://localhost:8000" />
  </AdminGuard>
} />
```

## 🔧 Usage Examples

### Recording Usage

```python
from core.usage_meter import record_token_usage, check_token_quota
from core.database import get_session

# Check quota before operation
allowed, error = check_token_quota(session, user_id, requested_tokens=1000)
if not allowed:
    raise HTTPException(status_code=403, detail=error)

# After operation, record usage
record_token_usage(
    session=session,
    user_id=user_id,
    tokens=500,
    metadata={"model": "gpt-4"}
)
```

### Checking Quotas

```python
from core.usage_meter import check_api_call_quota

allowed, error = check_api_call_quota(session, user_id)
if not allowed:
    return {"error": error}, 403
```

## 📊 Default Quota Limits

- **Basic**: 100K tokens, 1K API calls, 100 scraping tasks/month
- **Pro**: 1M tokens, 10K API calls, 1K scraping tasks/month
- **Enterprise**: Unlimited (0 = unlimited)

Customize in `BillingService.get_quota_limits_for_price()`

## 🧪 Testing

### Local Testing with Stripe CLI

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login: `stripe login`
3. Forward webhooks: `stripe listen --forward-to localhost:8000/api/billing/webhook`
4. Use test card: `4242 4242 4242 4242`

### Test Webhook Events

```bash
stripe trigger customer.subscription.created
stripe trigger invoice.paid
```

## 📚 Documentation

- `packages/core/BILLING_INTEGRATION.md` - Full integration guide
- `packages/core/BILLING_EXAMPLE.md` - Example integration

## 🔐 Security Notes

- Webhook endpoint verifies Stripe signatures
- All billing endpoints require authentication
- Admin endpoints require admin role
- Usage tracking is automatic and secure

## 🚀 Next Steps

1. Customize quota limits for your plans
2. Add more usage types if needed
3. Implement email notifications for quota warnings
4. Add analytics and reporting
5. Set up automated quota enforcement

## 📝 Notes

- Usage resets monthly at the start of each month
- Quota checking is optional but recommended
- All usage is tracked in the database for reporting
- Stripe handles all payment processing securely
