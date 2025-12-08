FROM python:3.11-slim

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
COPY pyproject.toml ./
COPY ../../packages/core/pyproject.toml ./packages/core/

# Install dependencies
RUN poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY . .

# Production server
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "app.main:app"]

