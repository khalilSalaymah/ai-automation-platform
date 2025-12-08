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

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

