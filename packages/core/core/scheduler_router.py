"""Scheduler API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlmodel import Session
from .logger import logger
from .scheduler_models import (
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    TaskExecutionResponse,
    TaskStatus,
)
from .scheduler import TaskScheduler
from .task_queue import TaskQueue
from .database import get_session
from .dependencies import get_current_active_user

router = APIRouter()


def get_scheduler() -> TaskScheduler:
    """Get scheduler instance."""
    return TaskScheduler()


def get_task_queue() -> TaskQueue:
    """Get task queue instance."""
    return TaskQueue()


@router.post("/tasks", response_model=ScheduledTaskResponse)
async def create_task(
    task: ScheduledTaskCreate,
    scheduler: TaskScheduler = Depends(get_scheduler),
    session: Session = Depends(get_session),
    _user=Depends(get_current_active_user),
):
    """Create a new scheduled task."""
    try:
        from .scheduler_models import ScheduledTask

        scheduled_task = ScheduledTask(
            id=f"{task.agent_name}:{task.task_name}",
            agent_name=task.agent_name,
            task_name=task.task_name,
            description=task.description,
            enabled=task.enabled,
            schedule=task.schedule,
            task_type=task.task_type,
            function_path=task.function_path,
            args=task.args,
            kwargs=task.kwargs,
        )
        success = scheduler.register_task(scheduled_task)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register task")

        return ScheduledTaskResponse.model_validate(scheduled_task)
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[ScheduledTaskResponse])
async def list_tasks(
    agent_name: Optional[str] = None,
    scheduler: TaskScheduler = Depends(get_scheduler),
    _user=Depends(get_current_active_user),
):
    """List all scheduled tasks."""
    try:
        tasks = scheduler.get_tasks(agent_name=agent_name)
        return [ScheduledTaskResponse.model_validate(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler),
    _user=Depends(get_current_active_user),
):
    """Get a scheduled task by ID."""
    try:
        task = scheduler.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return ScheduledTaskResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler),
    _user=Depends(get_current_active_user),
):
    """Delete a scheduled task."""
    try:
        success = scheduler.unregister_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/enable")
async def enable_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler),
    session: Session = Depends(get_session),
    _user=Depends(get_current_active_user),
):
    """Enable a scheduled task."""
    try:
        from .scheduler_models import ScheduledTask

        task = session.get(ScheduledTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.enabled = True
        session.commit()
        scheduler.register_task(task)
        return {"message": "Task enabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/disable")
async def disable_task(
    task_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler),
    session: Session = Depends(get_session),
    _user=Depends(get_current_active_user),
):
    """Disable a scheduled task."""
    try:
        from .scheduler_models import ScheduledTask

        task = session.get(ScheduledTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.enabled = False
        session.commit()
        scheduler.unregister_task(task_id)
        return {"message": "Task disabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions", response_model=List[TaskExecutionResponse])
async def list_executions(
    agent_name: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    _user=Depends(get_current_active_user),
):
    """List task executions."""
    try:
        from .scheduler_models import TaskExecution
        from sqlmodel import select

        query = select(TaskExecution)
        if agent_name:
            query = query.where(TaskExecution.agent_name == agent_name)
        if status:
            query = query.where(TaskExecution.status == status)
        query = query.order_by(TaskExecution.created_at.desc()).offset(offset).limit(limit)

        executions = session.exec(query).all()
        return [TaskExecutionResponse.model_validate(execution) for execution in executions]
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_execution(
    execution_id: str,
    task_queue: TaskQueue = Depends(get_task_queue),
    session: Session = Depends(get_session),
    _user=Depends(get_current_active_user),
):
    """Get a task execution by ID."""
    try:
        from .scheduler_models import TaskExecution

        # Update status from queue
        task_queue.update_execution_status(execution_id)

        execution = session.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        return TaskExecutionResponse.model_validate(execution)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    task_queue: TaskQueue = Depends(get_task_queue),
    _user=Depends(get_current_active_user),
):
    """Cancel a task execution."""
    try:
        success = task_queue.cancel(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")
        return {"message": "Execution cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

