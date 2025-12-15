"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # LLM provider configuration
    # For RAG chat: set LLM_PROVIDER=gemini and GEMINI_API_KEY
    llm_provider: str = ""
    gemini_api_key: str = ""

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
    secret_key: str = "your-secret-key-change-in-production"
    log_level: str = "INFO"

    # Vector Store
    vector_store: str = "pgvector"  # pgvector or pinecone

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

