"""Configuration management."""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)


class Settings(BaseSettings):
    """Application settings."""

    # LLM provider configuration
    # Text generation provider can be selected via environment (e.g. "groq", "gemini")
    llm_provider: str = ""
    gemini_api_key: str = ""

    # App metadata
    app_name: str = ""
    app_env: str = "development"

    # Vector store selection (e.g. "pgvector", "pinecone")
    vector_store: str = "pgvector"

    # OpenAI (only used for embeddings, not text generation)
    # Text generation uses LLM_PROVIDER (groq/gemini) from environment
    openai_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_agents"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    pinecone_environment: str = ""

    # Logging
    log_level: str = "INFO"
    
    # Observability
    slack_webhook_url: str = ""  # Slack webhook URL for error alerts
    enable_slack_alerts: bool = False  # Enable/disable Slack alerts

    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    frontend_url: str = "http://localhost:5173"

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_basic: str = ""  # Stripe Price ID for basic plan
    stripe_price_pro: str = ""  # Stripe Price ID for pro plan
    stripe_price_enterprise: str = ""  # Stripe Price ID for enterprise plan

    # Notion
    notion_api_key: str = ""  # Notion API key for importing pages
    notion_client_id: str = ""
    notion_client_secret: str = ""

    # Slack
    slack_client_id: str = ""
    slack_client_secret: str = ""

    # Microsoft/Outlook
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    # Airtable
    airtable_client_id: str = ""
    airtable_client_secret: str = ""

    # Shopify
    shopify_client_id: str = ""
    shopify_client_secret: str = ""
    shopify_shop_name: str = ""  # e.g., "my-shop" (without .myshopify.com)

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Ignore any extra environment variables not explicitly defined above
        extra = "ignore"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

