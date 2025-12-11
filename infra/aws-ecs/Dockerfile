# Dockerfile for AWS ECS Fargate deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
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

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
WORKDIR /app/packages/gateway
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "4", "app.main:app"]
