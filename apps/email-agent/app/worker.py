"""Background worker for email processing."""

from celery import Celery
from core.logger import logger
from .config import settings

celery_app = Celery(
    "email_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task
def process_email_async(email_data: dict):
    """
    Process email asynchronously.

    Args:
        email_data: Email data dictionary
    """
    try:
        from .services.email_service import EmailService

        service = EmailService()
        # Process email
        logger.info(f"Processing email asynchronously: {email_data.get('subject')}")
        # Implementation here
    except Exception as e:
        logger.error(f"Error in async email processing: {e}")
        raise

