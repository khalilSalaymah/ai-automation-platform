"""Database connection and session management."""

from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(settings.database_url, echo=False)


def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session



