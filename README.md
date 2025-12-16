# AI Automation Platform

A comprehensive monorepo for AI-powered automation agents with full authentication and multi-tenant support.

## 🏗️ Architecture

This monorepo contains:

- **Backend Apps**: FastAPI-based microservices for different AI agents
- **Frontend Apps**: React-based UIs for each agent
- **Shared Packages**: 
  - `packages/core`: Shared Python utilities, authentication, and database models
  - `packages/ui`: Shared React components and authentication hooks

## 📦 Applications

### Backend Services

1. **AIOps Bot** (`apps/aiops-bot`) - AI operations and monitoring
2. **Email Agent** (`apps/email-agent`) - AI-powered email automation
3. **RAG Chat** (`apps/rag-chat`) - Retrieval-Augmented Generation chat
4. **Scraper Agent** (`apps/scraper-agent`) - Web scraping automation
5. **Support Bot** (`apps/support-bot`) - AI customer support

### Frontend Applications

Each backend service has a corresponding React frontend application.

## 🔐 Authentication System

The platform includes a comprehensive authentication system with:

### Backend Features

- **JWT Authentication**: Secure token-based authentication
- **OAuth2 Google Login**: Social authentication via Google
- **Role-Based Access Control (RBAC)**: Three roles - `admin`, `client`, `staff`
- **Multi-Tenant Support**: Organization-based isolation using `org_id`
- **Password Hashing**: Bcrypt for secure password storage
- **Token Refresh**: Automatic token refresh mechanism

### Frontend Features

- **Login/Register Pages**: User authentication UI
- **Forgot Password**: Password reset flow
- **AuthGuard Component**: Route protection
- **useAuth Hook**: React hook for authentication state
- **Admin Protection**: Special guard for admin-only routes

### Authentication Flow

1. User registers or logs in via email/password or Google OAuth
2. Backend returns JWT access and refresh tokens
3. Frontend stores tokens in localStorage
4. All API requests include the access token in the Authorization header
5. Tokens are automatically refreshed when expired

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional, for session management)

### Backend Setup

1. **Install dependencies** for the core package:
   ```bash
   cd packages/core
   poetry install
   ```

2. **Install dependencies** for each app:
   ```bash
   cd apps/aiops-bot  # or any other app
   poetry install
   ```

3. **Configure environment variables**:
   Create a `.env` file in each app directory:
   ```env
   # Database
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_agents
   
   # JWT Secret (change in production!)
   SECRET_KEY=your-secret-key-change-in-production
   
   # Google OAuth (optional)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
   
   # Frontend URL
   FRONTEND_URL=http://localhost:5173
   
   # OpenAI (for AI features)
   OPENAI_API_KEY=your-openai-api-key
   ```

4. **Initialize the database**:
   The database tables are automatically created on app startup via `init_db()`.

5. **Run a backend service**:
   ```bash
   cd apps/aiops-bot
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install dependencies** for the UI package:
   ```bash
   cd packages/ui
   npm install
   ```

2. **Install dependencies** for each frontend app:
   ```bash
   cd apps/aiops-bot/frontend
   npm install
   ```

3. **Configure API URL** (optional):
   Create a `.env` file:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Run a frontend app**:
   ```bash
   cd apps/aiops-bot/frontend
   npm run dev
   ```

## 📚 Usage

### Backend: Protecting Routes

```python
from fastapi import Depends
from core import get_current_active_user, RequireAdmin, User

# Require authentication
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user.email}

# Require admin role
@router.get("/admin-only")
async def admin_route(current_user: User = RequireAdmin):
    return {"message": "Admin access granted"}
```

### Frontend: Using Authentication

```jsx
import { useAuth, AuthGuard, AdminGuard } from '@ui/components'

// In a component
function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth()
  
  return (
    <div>
      {isAuthenticated ? (
        <div>
          <p>Welcome, {user.email}</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={() => login('email@example.com', 'password')}>
          Login
        </button>
      )}
    </div>
  )
}

// Protect routes
function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route 
        path="/dashboard" 
        element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        } 
      />
      <Route 
        path="/admin" 
        element={
          <AdminGuard>
            <AdminPanel />
          </AdminGuard>
        } 
      />
    </Routes>
  )
}
```

## 🔧 API Endpoints

### Authentication Endpoints

All apps include the following auth endpoints at `/api/auth`:

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/forgot-password` - Request password reset
- `GET /api/auth/google/login` - Initiate Google OAuth
- `GET /api/auth/google/callback` - Google OAuth callback

## 🗄️ Database Models

### User Model

- `id`: UUID primary key
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password (null for OAuth users)
- `full_name`: User's full name
- `role`: Enum (`admin`, `client`, `staff`)
- `org_id`: Organization ID for multi-tenancy
- `google_id`: Google OAuth ID (if using Google login)
- `is_active`: Account status
- `is_verified`: Email verification status
- `avatar_url`: Profile picture URL
- `created_at`, `updated_at`: Timestamps

### Organization Model

- `id`: UUID primary key
- `name`: Organization name
- `slug`: Unique slug for URL routing
- `created_at`, `updated_at`: Timestamps

## 🔒 Security Best Practices

1. **Change the SECRET_KEY** in production - use a strong, random secret
2. **Use HTTPS** in production
3. **Configure CORS** appropriately for your domain
4. **Set strong password requirements** (minimum 8 characters enforced)
5. **Implement rate limiting** for auth endpoints
6. **Use environment variables** for all secrets
7. **Regularly rotate JWT secrets**

## 🏢 Multi-Tenancy

The platform supports multi-tenancy through the `org_id` field:

- Users belong to an organization via `org_id`
- Filter data by organization in your queries
- Use `get_user_org_id()` dependency to get the current user's org

Example:
```python
from core import get_user_org_id

@router.get("/data")
async def get_data(org_id: str = Depends(get_user_org_id)):
    # Filter data by organization
    data = session.exec(select(Data).where(Data.org_id == org_id))
    return data
```

## 🧪 Testing

Run tests for each package:

```bash
# Core package
cd packages/core
poetry run pytest

# App tests
cd apps/aiops-bot
poetry run pytest
```

## 📝 Development

### Adding a New App

1. Copy an existing app structure
2. Update `app/main.py` to include the auth router:
   ```python
   from core import auth_router, init_db
   
   app.include_router(auth_router, prefix="/api")
   ```
3. Update frontend `App.jsx` to use `AuthProvider` and `AuthGuard`
4. Configure Vite alias for `@ui/components`

### Project Structure

```
.
├── apps/                    # Application services
│   ├── aiops-bot/
│   │   ├── app/            # Backend code
│   │   └── frontend/       # Frontend code
│   └── ...
├── packages/
│   ├── core/               # Shared Python package
│   │   └── core/
│   │       ├── auth.py     # Auth utilities
│   │       ├── models.py   # Database models
│   │       ├── auth_router.py  # Auth endpoints
│   │       └── dependencies.py # FastAPI dependencies
│   └── ui/                 # Shared React components
│       └── src/
│           ├── components/ # Auth components
│           └── hooks/       # useAuth hook
└── README.md
```

## 🐛 Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database exists: `createdb ai_agents`

### Authentication Not Working

- Check JWT secret key is set
- Verify tokens are being sent in requests
- Check browser console for errors
- Verify API URL is correct in frontend

### OAuth Not Working

- Ensure Google OAuth credentials are set
- Check redirect URI matches Google Console settings
- Verify `FRONTEND_URL` is correct

## 📄 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]





