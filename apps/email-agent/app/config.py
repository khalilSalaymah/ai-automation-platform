"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # LLM provider is detected from LLM_PROVIDER env var (groq or gemini)
    # For Groq: set LLM_PROVIDER=groq and GROQ_API_KEY
    # For Gemini: set LLM_PROVIDER=gemini and GEMINI_API_KEY

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

