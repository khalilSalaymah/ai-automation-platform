"""Background worker."""

from celery import Celery
from .config import settings

celery_app = Celery("support_bot", broker=settings.redis_url, backend=settings.redis_url)

