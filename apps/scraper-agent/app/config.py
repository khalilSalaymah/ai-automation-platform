"""Config."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider is detected from LLM_PROVIDER env var (groq or gemini)
    # For Groq: set LLM_PROVIDER=groq and GROQ_API_KEY
    # For Gemini: set LLM_PROVIDER=gemini and GEMINI_API_KEY
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_agents"

    class Config:
        env_file = ".env"


settings = Settings()

