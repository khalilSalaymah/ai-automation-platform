# Multi-stage Dockerfile for Fly.io deployment
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry>=1.5.0
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY packages/core/pyproject.toml ./packages/core/
COPY packages/gateway/pyproject.toml ./packages/gateway/

# Install core dependencies
WORKDIR /app/packages/core
RUN poetry install --no-interaction --no-ansi --only main

# Install gateway dependencies
WORKDIR /app/packages/gateway
RUN poetry install --no-interaction --no-ansi --only main

# Copy application code
WORKDIR /app
COPY packages/core ./packages/core
COPY packages/gateway ./packages/gateway

# Frontend build stage
FROM node:18-alpine as frontend-builder

WORKDIR /app
COPY packages/ui/package.json packages/ui/package-lock.json* ./packages/ui/
WORKDIR /app/packages/ui
RUN npm ci

COPY packages/ui .
RUN npm run build

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend /app /app

# Copy frontend
COPY --from=frontend-builder /app/packages/ui/dist /usr/share/nginx/html

# Copy nginx config
COPY infra/frontend/nginx.conf /etc/nginx/sites-available/default

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
# Start nginx in background\n\
nginx\n\
# Start backend\n\
cd /app/packages/gateway\n\
exec gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --workers 4 app.main:app\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
