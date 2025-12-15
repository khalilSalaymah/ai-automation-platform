FROM python:3.11-slim

WORKDIR /app

# Name of the app directory under ./apps (e.g. rag-chat, email-agent)
ARG APP_NAME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry>=1.5.0
RUN poetry config virtualenvs.create false

# Copy dependency files for the selected app and shared core package
COPY ./apps/${APP_NAME}/pyproject.toml ./
COPY ./packages/core /packages/core

# Install dependencies (app + core) without installing the app itself as a package
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Copy application and shared core code into the image
COPY ./apps/${APP_NAME} .
COPY ./packages/core ./packages/core

# Production server (expects FastAPI app in app/main.py inside the app directory)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "app.main:app"]