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

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_index: Optional[str] = None
    pinecone_environment: Optional[str] = None

    # Application
    app_name: str = "rag-chat"
    app_env: str = "development"
    log_level: str = "INFO"

    # Vector Store
    vector_store: str = "pgvector"  # pgvector or pinecone

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

