# Render.com Deployment Guide

This guide will help you deploy the AI Automation Platform to Render.com.

## Prerequisites

1. Sign up for a [Render.com account](https://render.com)
2. Install [Render CLI](https://render.com/docs/cli) (optional, for CLI deployment)

## Quick Deploy via Dashboard

### 1. Create Blueprint

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your Git repository
4. Select the repository and branch
5. Render will detect `render.yaml` automatically

### 2. Configure Environment Variables

After the blueprint is created, set these environment variables in the dashboard:

**Gateway Service:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `FRONTEND_URL` - Your frontend service URL (e.g., `https://ai-automation-frontend.onrender.com`)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID (optional)
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret (optional)
- `GOOGLE_REDIRECT_URI` - `https://your-gateway-service.onrender.com/api/auth/google/callback`

**Frontend Service:**
- `VITE_API_URL` - Your gateway service URL (e.g., `https://ai-automation-gateway.onrender.com`)

### 3. Deploy

Click "Apply" in the Blueprint view. Render will:
- Create PostgreSQL database
- Create Redis instance
- Deploy gateway service
- Deploy frontend service
- Link all services together

## Quick Deploy via CLI

### 1. Login to Render

```bash
render login
```

### 2. Deploy Blueprint

```bash
cd infra/render
render blueprint launch
```

Follow the prompts to:
- Select your Git repository
- Choose a region
- Set environment variables

## Manual Service Creation

If you prefer to create services manually:

### 1. Create PostgreSQL Database

1. Go to Dashboard → "New +" → "PostgreSQL"
2. Name: `ai-automation-db`
3. Database: `ai_agents`
4. Region: Choose closest to you
5. Plan: Starter (for development)

### 2. Create Redis Instance

1. Go to Dashboard → "New +" → "Redis"
2. Name: `ai-automation-redis`
3. Region: Same as database
4. Plan: Starter

### 3. Create Gateway Service

1. Go to Dashboard → "New +" → "Web Service"
2. Connect your Git repository
3. Settings:
   - **Name**: `ai-automation-gateway`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `infra/render`
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `../..`
   - **Plan**: Starter
4. Environment Variables:
   - `DATABASE_URL` - From PostgreSQL service (auto-linked)
   - `REDIS_URL` - From Redis service (auto-linked)
   - `SECRET_KEY` - Generate a random string
   - `OPENAI_API_KEY` - Your OpenAI key
   - `FRONTEND_URL` - Your frontend URL
   - `SERVICE_PORT` - `8080`
   - `SERVICE_HOST` - `0.0.0.0`

### 4. Create Frontend Service

1. Go to Dashboard → "New +" → "Static Site" or "Web Service"
2. For Static Site:
   - Connect Git repository
   - Root Directory: `packages/ui`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
3. For Web Service (Docker):
   - Use `frontend.Dockerfile`
   - Set `VITE_API_URL` environment variable

## Environment Variables Reference

### Gateway Service

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (auto-set) |
| `REDIS_URL` | Yes | Redis connection string (auto-set) |
| `SECRET_KEY` | Yes | JWT secret key |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `FRONTEND_URL` | Yes | Frontend application URL |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | No | OAuth redirect URI |
| `SERVICE_PORT` | No | Port to run on (default: 8080) |
| `SERVICE_HOST` | No | Host to bind to (default: 0.0.0.0) |

### Frontend Service

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL |

## Custom Domain

1. Go to your service → Settings → "Custom Domains"
2. Add your domain
3. Follow DNS configuration instructions
4. Render will automatically provision SSL certificates

## Scaling

### Vertical Scaling

1. Go to service → Settings → "Plan"
2. Upgrade to Standard or Pro plan

### Horizontal Scaling

Render automatically handles load balancing. For high availability:
- Use Pro plan with multiple instances
- Enable "Auto-Deploy" for zero-downtime deployments

## Monitoring

- **Logs**: View real-time logs in the dashboard
- **Metrics**: CPU, Memory, Request metrics available
- **Alerts**: Set up email/Slack alerts for service issues

## Troubleshooting

### Service Won't Start

1. Check logs in the dashboard
2. Verify environment variables are set
3. Check database connectivity
4. Verify Dockerfile builds correctly

### Database Connection Issues

1. Verify `DATABASE_URL` is set correctly
2. Check database is running
3. Verify network connectivity (services in same region)

### Build Failures

1. Check build logs
2. Verify Dockerfile paths are correct
3. Ensure all dependencies are in `pyproject.toml` or `package.json`

## Cost Optimization

- Use Starter plans for development
- Enable "Auto-Suspend" for non-production services
- Use Render's free tier for testing
- Monitor usage in the dashboard

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)
