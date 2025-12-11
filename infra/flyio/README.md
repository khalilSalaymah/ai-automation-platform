# Fly.io Deployment Guide

This guide will help you deploy the AI Automation Platform to Fly.io.

## Prerequisites

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. Sign up for a [Fly.io account](https://fly.io/app/sign-up)
3. Login: `flyctl auth login`

## Quick Deploy

### 1. Initialize Fly.io App

```bash
cd infra/flyio
flyctl launch --no-deploy
```

This creates a `fly.toml` file. The provided `fly.toml` is already configured.

### 2. Create PostgreSQL Database

```bash
flyctl postgres create --name ai-automation-db --region iad
flyctl postgres attach ai-automation-db
```

### 3. Create Redis Instance

```bash
flyctl redis create --name ai-automation-redis --region iad
```

### 4. Set Secrets

```bash
# Get database URL from postgres info
flyctl postgres connect -a ai-automation-db

# Set secrets
flyctl secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  OPENAI_API_KEY="your-openai-api-key" \
  FRONTEND_URL="https://your-app.fly.dev" \
  GOOGLE_CLIENT_ID="your-google-client-id" \
  GOOGLE_CLIENT_SECRET="your-google-client-secret" \
  GOOGLE_REDIRECT_URI="https://your-app.fly.dev/api/auth/google/callback"
```

The `DATABASE_URL` and `REDIS_URL` are automatically set when you attach the services.

### 5. Deploy

```bash
flyctl deploy
```

### 6. Check Status

```bash
flyctl status
flyctl logs
```

## Environment Variables

Required environment variables (set via `flyctl secrets set`):

- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)
- `OPENAI_API_KEY` - OpenAI API key
- `FRONTEND_URL` - Your app URL (e.g., `https://your-app.fly.dev`)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID (optional)
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret (optional)
- `GOOGLE_REDIRECT_URI` - Google OAuth redirect URI

Automatically set:
- `DATABASE_URL` - Set when PostgreSQL is attached
- `REDIS_URL` - Set when Redis is attached

## Scaling

```bash
# Scale to 2 instances
flyctl scale count 2

# Scale memory
flyctl scale vm memory 1024
```

## Monitoring

```bash
# View logs
flyctl logs

# View metrics
flyctl metrics

# SSH into instance
flyctl ssh console
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database status
flyctl postgres status -a ai-automation-db

# Connect to database
flyctl postgres connect -a ai-automation-db
```

### View Application Logs

```bash
flyctl logs
```

### Restart Application

```bash
flyctl apps restart
```

## Custom Domain

```bash
# Add custom domain
flyctl certs add yourdomain.com

# Check certificate status
flyctl certs show yourdomain.com
```

## Cost Optimization

- Use `auto_stop_machines = true` to stop machines when idle
- Start with shared-cpu-1x (512MB) and scale as needed
- Use Fly.io's free tier for development
