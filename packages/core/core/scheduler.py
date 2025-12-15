"""Task scheduler for managing scheduled tasks."""

import yaml
import importlib
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
from croniter import croniter
import redis
from rq import Queue
from .logger import logger
from .config import get_settings
from .scheduler_models import ScheduledTask, TaskStatus
from .task_queue import TaskQueue
from .database import get_session

settings = get_settings()


class TaskScheduler:
    """Manages scheduled tasks and their execution."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize scheduler.

        Args:
            redis_url: Redis connection URL. Defaults to settings.redis_url
        """
        self.redis_url = redis_url or settings.redis_url
        self.task_queue = TaskQueue(redis_url=redis_url)
        self.redis_conn = redis.from_url(self.redis_url)
        self.scheduled_jobs: Dict[str, Any] = {}  # Store RQ scheduled jobs

    def load_tasks_from_yaml(self, yaml_path: str, agent_name: str) -> List[ScheduledTask]:
        """
        Load scheduled tasks from YAML file.

        Args:
            yaml_path: Path to YAML file
            agent_name: Name of the agent

        Returns:
            List of ScheduledTask objects
        """
        tasks = []
        yaml_file = Path(yaml_path)

        if not yaml_file.exists():
            logger.warning(f"YAML file not found: {yaml_path}")
            return tasks

        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            if not data or "tasks" not in data:
                logger.warning(f"No tasks found in {yaml_path}")
                return tasks

            for task_data in data["tasks"]:
                task = ScheduledTask(
                    id=f"{agent_name}:{task_data['name']}",
                    agent_name=agent_name,
                    task_name=task_data["name"],
                    description=task_data.get("description"),
                    enabled=task_data.get("enabled", True),
                    schedule=task_data["schedule"],
                    task_type=task_data.get("type", "cron"),
                    function_path=task_data["function"],
                    args=task_data.get("args"),
                    kwargs=task_data.get("kwargs"),
                )
                tasks.append(task)

            logger.info(f"Loaded {len(tasks)} tasks from {yaml_path}")
        except Exception as e:
            logger.error(f"Error loading tasks from {yaml_path}: {e}")

        return tasks

    def register_task(self, task: ScheduledTask) -> bool:
        """
        Register a scheduled task.

        Args:
            task: ScheduledTask object

        Returns:
            True if registered successfully
        """
        if not task.enabled:
            logger.info(f"Task {task.task_name} is disabled, skipping")
            return False

        try:
            # Save to database
            with next(get_session()) as session:
                existing = session.get(ScheduledTask, task.id)
                if existing:
                    # Update existing
                    for key, value in task.model_dump(exclude={"id", "created_at"}).items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    session.commit()
                    # Use a plain dict so we don't keep a session-bound instance
                    task_data = existing.model_dump()
                else:
                    session.add(task)
                    session.commit()
                    session.refresh(task)
                    task_data = task.model_dump()

            # Work with a detached instance (not bound to a DB session) to avoid
            # DetachedInstanceError during scheduling.
            detached_task = ScheduledTask(**task_data)

            # Schedule the task
            self._schedule_task(detached_task)
            logger.info(f"Registered task {detached_task.task_name} for agent {detached_task.agent_name}")
            return True
        except Exception as e:
            task_name = getattr(task, "task_name", getattr(task, "id", "unknown"))
            logger.error(f"Error registering task {task_name}: {e}")
            return False

    def _schedule_task(self, task: ScheduledTask) -> None:
        """
        Schedule a task using RQ scheduler.

        Args:
            task: ScheduledTask object
        """
        try:
            # Import the function
            func = self._import_function(task.function_path)

            # Parse schedule
            if task.task_type == "cron":
                # Validate cron expression
                if not croniter.is_valid(task.schedule):
                    logger.error(f"Invalid cron expression: {task.schedule}")
                    return

                # Use RQ's cron scheduling
                from rq_scheduler import Scheduler

                scheduler = Scheduler(queue=self.task_queue.queue, connection=self.redis_conn)
                # Handle args - if it's a dict, convert to tuple of values, otherwise use as-is
                if task.args:
                    if isinstance(task.args, dict):
                        args = tuple(task.args.values())
                    else:
                        args = tuple(task.args) if isinstance(task.args, list) else (task.args,)
                else:
                    args = ()
                
                job = scheduler.cron(
                    cron_string=task.schedule,
                    func=func,
                    args=args,
                    kwargs=task.kwargs or {},
                    job_id=f"{task.id}:{datetime.utcnow().timestamp()}",
                    meta={
                        "agent_name": task.agent_name,
                        "task_name": task.task_name,
                        "function_path": task.function_path,
                        "scheduled_task_id": task.id,
                    },
                )
                self.scheduled_jobs[task.id] = job
                logger.info(f"Scheduled cron task {task.task_name} with schedule {task.schedule}")

            elif task.task_type == "interval":
                # Parse interval (e.g., "5 minutes", "1 hour")
                from rq_scheduler import Scheduler
                import re

                scheduler = Scheduler(queue=self.task_queue.queue, connection=self.redis_conn)
                # Parse interval string
                interval_match = re.match(r"(\d+)\s*(second|minute|hour|day|week)s?", task.schedule.lower())
                if interval_match:
                    value, unit = interval_match.groups()
                    value = int(value)
                    # Convert to seconds
                    unit_map = {
                        "second": 1,
                        "minute": 60,
                        "hour": 3600,
                        "day": 86400,
                        "week": 604800,
                    }
                    seconds = value * unit_map.get(unit, 1)
                    # Handle args - if it's a dict, convert to tuple of values, otherwise use as-is
                    if task.args:
                        if isinstance(task.args, dict):
                            args = tuple(task.args.values())
                        else:
                            args = tuple(task.args) if isinstance(task.args, list) else (task.args,)
                    else:
                        args = ()
                    
                    job = scheduler.schedule(
                        scheduled_time=datetime.utcnow(),
                        func=func,
                        args=args,
                        kwargs=task.kwargs or {},
                        interval=seconds,
                        job_id=f"{task.id}:{datetime.utcnow().timestamp()}",
                        meta={
                            "agent_name": task.agent_name,
                            "task_name": task.task_name,
                            "function_path": task.function_path,
                            "scheduled_task_id": task.id,
                        },
                    )
                    self.scheduled_jobs[task.id] = job
                    logger.info(f"Scheduled interval task {task.task_name} with interval {task.schedule}")
                else:
                    logger.error(f"Invalid interval format: {task.schedule}")

        except Exception as e:
            task_name = getattr(task, "task_name", getattr(task, "id", "unknown"))
            logger.error(f"Error scheduling task {task_name}: {e}")

    def _import_function(self, function_path: str) -> Callable:
        """
        Import function from path string.

        Args:
            function_path: Path like "module.path:function_name"

        Returns:
            Callable function
        """
        module_path, function_name = function_path.split(":")
        module = importlib.import_module(module_path)
        return getattr(module, function_name)

    def unregister_task(self, task_id: str) -> bool:
        """
        Unregister a scheduled task.

        Args:
            task_id: Task ID

        Returns:
            True if unregistered successfully
        """
        try:
            # Cancel scheduled job
            if task_id in self.scheduled_jobs:
                job = self.scheduled_jobs[task_id]
                job.cancel()
                del self.scheduled_jobs[task_id]

            # Update database
            with next(get_session()) as session:
                task = session.get(ScheduledTask, task_id)
                if task:
                    task.enabled = False
                    session.commit()

            logger.info(f"Unregistered task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error unregistering task {task_id}: {e}")
            return False

    def get_tasks(self, agent_name: Optional[str] = None) -> List[ScheduledTask]:
        """
        Get all scheduled tasks.

        Args:
            agent_name: Filter by agent name, or None for all

        Returns:
            List of ScheduledTask objects
        """
        from sqlmodel import select
        
        with next(get_session()) as session:
            query = select(ScheduledTask)
            if agent_name:
                query = query.where(ScheduledTask.agent_name == agent_name)
            return list(session.exec(query).all())

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        Get a scheduled task by ID.

        Args:
            task_id: Task ID

        Returns:
            ScheduledTask or None
        """
        with next(get_session()) as session:
            return session.get(ScheduledTask, task_id)

