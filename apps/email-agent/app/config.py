"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_agents"

    # Application
    app_name: str = "email-agent"
    app_env: str = "development"
    log_level: str = "INFO"

    # Email
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

