"""RQ worker for processing background tasks."""

import sys
from rq import Worker, Queue, Connection
from redis import Redis
from .config import get_settings
from .logger import logger

settings = get_settings()


def create_worker(queue_name: str = "default"):
    """
    Create and run an RQ worker.
    
    Args:
        queue_name: Name of the queue to process
    """
    redis_conn = Redis.from_url(settings.redis_url)
    
    with Connection(redis_conn):
        worker = Worker([Queue(queue_name, connection=redis_conn)])
        logger.info(f"Starting RQ worker for queue: {queue_name}")
        worker.work()


if __name__ == "__main__":
    queue_name = sys.argv[1] if len(sys.argv) > 1 else "default"
    create_worker(queue_name)

