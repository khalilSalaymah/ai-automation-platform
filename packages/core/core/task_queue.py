"""Task queue using Redis Queue (RQ)."""

import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from rq import Queue
from rq.job import Job, JobStatus
import redis
from .logger import logger
from .config import get_settings
from .scheduler_models import TaskStatus, TaskExecution
from .database import get_session

settings = get_settings()


class TaskQueue:
    """Redis Queue wrapper for task management."""

    def __init__(self, redis_url: Optional[str] = None, queue_name: str = "default"):
        """
        Initialize task queue.

        Args:
            redis_url: Redis connection URL. Defaults to settings.redis_url
            queue_name: Name of the queue
        """
        self.redis_url = redis_url or settings.redis_url
        self.queue_name = queue_name
        self.redis_conn = redis.from_url(self.redis_url)
        self.queue = Queue(queue_name, connection=self.redis_conn)

    def enqueue(
        self,
        func: Callable,
        agent_name: str,
        task_name: str,
        function_path: str,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        scheduled_task_id: Optional[str] = None,
    ) -> str:
        """
        Enqueue a task.

        Args:
            func: Function to execute
            agent_name: Name of the agent
            task_name: Name of the task
            function_path: Path to the function (for tracking)
            args: Function arguments
            kwargs: Function keyword arguments
            scheduled_task_id: ID of the scheduled task if applicable

        Returns:
            Task execution ID
        """
        job_id = str(uuid.uuid4())
        args = args or ()
        kwargs = kwargs or {}

        # Create job with metadata
        job = self.queue.enqueue(
            func,
            *args,
            **kwargs,
            job_id=job_id,
            meta={
                "agent_name": agent_name,
                "task_name": task_name,
                "function_path": function_path,
                "scheduled_task_id": scheduled_task_id,
            },
        )

        # Create execution record
        execution = TaskExecution(
            id=job_id,
            task_id=job_id,
            scheduled_task_id=scheduled_task_id,
            agent_name=agent_name,
            task_name=task_name,
            status=TaskStatus.QUEUED,
            function_path=function_path,
            args=dict(enumerate(args)) if args else None,
            kwargs=kwargs,
        )

        with next(get_session()) as session:
            session.add(execution)
            session.commit()

        logger.info(f"Enqueued task {task_name} for agent {agent_name} with ID {job_id}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job object or None
        """
        try:
            return Job.fetch(job_id, connection=self.redis_conn)
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return None

    def get_status(self, job_id: str) -> Optional[TaskStatus]:
        """
        Get task status.

        Args:
            job_id: Job ID

        Returns:
            Task status or None
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Map RQ status to our TaskStatus
        status_map = {
            JobStatus.QUEUED: TaskStatus.QUEUED,
            JobStatus.STARTED: TaskStatus.RUNNING,
            JobStatus.FINISHED: TaskStatus.SUCCESS,
            JobStatus.FAILED: TaskStatus.FAILED,
        }
        return status_map.get(job.get_status(), TaskStatus.QUEUED)

    def update_execution_status(self, job_id: str) -> None:
        """
        Update execution record from job status.

        Args:
            job_id: Job ID
        """
        job = self.get_job(job_id)
        if not job:
            return

        with next(get_session()) as session:
            execution = session.get(TaskExecution, job_id)
            if not execution:
                return

            status = self.get_status(job_id)
            if status:
                execution.status = status

            if job.started_at:
                execution.started_at = job.started_at

            if job.ended_at:
                execution.completed_at = job.ended_at

            if job.is_finished:
                try:
                    result = job.result
                    execution.result = {"result": str(result)} if result else None
                except Exception:
                    pass

            if job.is_failed:
                execution.error = str(job.exc_info) if job.exc_info else "Unknown error"

            execution.updated_at = datetime.utcnow()
            session.commit()

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False otherwise
        """
        job = self.get_job(job_id)
        if not job:
            return False

        try:
            job.cancel()
            with next(get_session()) as session:
                execution = session.get(TaskExecution, job_id)
                if execution:
                    execution.status = TaskStatus.CANCELLED
                    execution.completed_at = datetime.utcnow()
                    session.commit()
            return True
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    def get_result(self, job_id: str) -> Optional[Any]:
        """
        Get job result.

        Args:
            job_id: Job ID

        Returns:
            Job result or None
        """
        job = self.get_job(job_id)
        if not job:
            return None

        try:
            return job.result
        except Exception:
            return None

