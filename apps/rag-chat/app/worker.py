"""Background worker for RAG processing."""

from celery import Celery
from core.logger import logger
from .config import settings

celery_app = Celery(
    "rag_chat",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task
def index_document_async(filename: str, content: bytes):
    """Index document asynchronously."""
    try:
        from .services.rag_service import RAGService
        service = RAGService()
        logger.info(f"Indexing document asynchronously: {filename}")
        # Implementation here
    except Exception as e:
        logger.error(f"Error in async document indexing: {e}")
        raise

