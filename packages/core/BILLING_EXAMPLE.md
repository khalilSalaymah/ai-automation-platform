# Example: Integrating Billing into an App

This example shows how to integrate billing into the RAG Chat app.

## Backend Changes

### 1. Update `apps/rag-chat/app/main.py`

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.logger import logger
from core import auth_router, billing_router, init_db  # Add billing_router

load_dotenv()

from .routers.rag_router import router as rag_router
from .config import settings

app = FastAPI(
    title="RAG Chat API",
    description="Retrieval-Augmented Generation chat",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include billing router
app.include_router(billing_router, prefix="/api")  # Add this line

# Include app routers
app.include_router(rag_router, prefix="/api", tags=["rag"])

# ... rest of the file
```

### 2. Update `apps/rag-chat/app/routers/rag_router.py`

Add usage tracking to your endpoints:

```python
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from core.database import get_session
from core.dependencies import get_current_active_user
from core.models import User
from core.usage_meter import (
    check_token_quota,
    record_token_usage,
    record_api_call_usage,
)

@router.post("/chat")
async def chat(
    message: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Chat endpoint with usage tracking."""
    
    # Check API call quota
    allowed, error = check_api_call_quota(session, current_user.id)
    if not allowed:
        raise HTTPException(status_code=403, detail=error)
    
    # Estimate tokens (you can use tiktoken for accurate counting)
    estimated_tokens = len(message.split()) * 1.3  # Rough estimate
    
    # Check token quota
    allowed, error = check_token_quota(session, current_user.id, int(estimated_tokens))
    if not allowed:
        raise HTTPException(status_code=403, detail=error)
    
    # Process chat request
    # ... your LLM call here ...
    response = llm.generate(message)
    tokens_used = response.usage.total_tokens  # Get actual tokens from LLM response
    
    # Record usage
    record_api_call_usage(
        session=session,
        user_id=current_user.id,
        metadata={"endpoint": "/api/chat", "model": "gpt-4"}
    )
    
    record_token_usage(
        session=session,
        user_id=current_user.id,
        tokens=tokens_used,
        metadata={"model": "gpt-4", "prompt_tokens": response.usage.prompt_tokens}
    )
    
    return {"response": response.text}
```

## Frontend Changes

### 1. Update `apps/rag-chat/frontend/src/App.jsx`

Add billing route:

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, AuthGuard, AdminGuard } from '@ui/components';
import { BillingDashboard, BillingAdmin } from '@ui/components';
import Chat from './pages/Chat';
import AuthCallback from './pages/AuthCallback';

function App() {
  return (
    <AuthProvider apiUrl="http://localhost:8000">
      <BrowserRouter>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route
            path="/"
            element={
              <AuthGuard>
                <Chat />
              </AuthGuard>
            }
          />
          <Route
            path="/billing"
            element={
              <AuthGuard>
                <BillingDashboard apiUrl="http://localhost:8000" />
              </AuthGuard>
            }
          />
          <Route
            path="/admin/billing"
            element={
              <AdminGuard>
                <BillingAdmin apiUrl="http://localhost:8000" />
              </AdminGuard>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

### 2. Add Navigation Link

In your navigation component:

```jsx
<Link to="/billing" className="nav-link">
  Billing
</Link>
```

## Environment Variables

Add to `apps/rag-chat/.env`:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

## Testing

1. Start your app
2. Create a test subscription using Stripe test mode
3. Make API calls and verify usage is tracked
4. Check the billing dashboard to see usage
