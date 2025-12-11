"""Gateway configuration."""

import os
from typing import Dict
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class GatewaySettings(BaseSettings):
    """Gateway service settings."""

    # Service configuration
    service_name: str = "gateway"
    service_port: int = 8080
    service_host: str = "0.0.0.0"

    # Agent service URLs (internal)
    email_agent_url: str = os.getenv("EMAIL_AGENT_URL", "http://localhost:8081")
    rag_agent_url: str = os.getenv("RAG_AGENT_URL", "http://localhost:8082")
    scraper_agent_url: str = os.getenv("SCRAPER_AGENT_URL", "http://localhost:8083")
    support_agent_url: str = os.getenv("SUPPORT_AGENT_URL", "http://localhost:8084")
    aiops_agent_url: str = os.getenv("AIOPS_AGENT_URL", "http://localhost:8085")

    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

    # Request timeout
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # Database (for quota checking)
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_agents"
    )

    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> GatewaySettings:
    """Get gateway settings."""
    return GatewaySettings()


def get_agent_urls() -> Dict[str, str]:
    """Get mapping of agent names to their URLs."""
    settings = get_settings()
    return {
        "email": settings.email_agent_url,
        "rag": settings.rag_agent_url,
        "scraper": settings.scraper_agent_url,
        "support": settings.support_agent_url,
        "aiops": settings.aiops_agent_url,
    }
