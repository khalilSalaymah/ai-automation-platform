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

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

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

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

