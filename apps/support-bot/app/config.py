"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider is detected from LLM_PROVIDER env var (groq or gemini)
    # For Groq: set LLM_PROVIDER=groq and GROQ_API_KEY
    # For Gemini: set LLM_PROVIDER=gemini and GEMINI_API_KEY
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_agents"
    app_name: str = "support-bot"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

