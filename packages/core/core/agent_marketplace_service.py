"""Agent marketplace service for managing agent deployments."""

from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from uuid import uuid4
from datetime import datetime
from .logger import logger
from .agent_marketplace_models import (
    Agent,
    OrganizationAgent,
    AgentStatus,
)
from .scheduler import TaskScheduler
from .scheduler_models import ScheduledTask
from .task_queue import TaskQueue


class AgentMarketplaceService:
    """Service for managing agent marketplace and deployments."""

    def __init__(self):
        """Initialize service."""
        self.scheduler = TaskScheduler()
        self.task_queue = TaskQueue()

    def list_agents(
        self, session: Session, category: Optional[str] = None, is_active: bool = True
    ) -> List[Agent]:
        """
        List all available agents.

        Args:
            session: Database session
            category: Optional category filter
            is_active: Filter by active status

        Returns:
            List of Agent objects
        """
        query = select(Agent)
        if category:
            query = query.where(Agent.category == category)
        if is_active is not None:
            query = query.where(Agent.is_active == is_active)

        return list(session.exec(query).all())

    def get_agent(self, session: Session, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID.

        Args:
            session: Database session
            agent_id: Agent ID

        Returns:
            Agent object or None
        """
        return session.get(Agent, agent_id)

    def get_agent_by_name(self, session: Session, agent_name: str) -> Optional[Agent]:
        """
        Get agent by name.

        Args:
            session: Database session
            agent_name: Agent name

        Returns:
            Agent object or None
        """
        query = select(Agent).where(Agent.name == agent_name)
        return session.exec(query).first()

    def list_organization_agents(
        self, session: Session, org_id: str
    ) -> List[OrganizationAgent]:
        """
        List agents deployed for an organization.

        Args:
            session: Database session
            org_id: Organization ID

        Returns:
            List of OrganizationAgent objects
        """
        query = select(OrganizationAgent).where(OrganizationAgent.org_id == org_id)
        return list(session.exec(query).all())

    def get_organization_agent(
        self, session: Session, org_id: str, agent_id: str
    ) -> Optional[OrganizationAgent]:
        """
        Get organization agent deployment.

        Args:
            session: Database session
            org_id: Organization ID
            agent_id: Agent ID

        Returns:
            OrganizationAgent object or None
        """
        query = (
            select(OrganizationAgent)
            .where(OrganizationAgent.org_id == org_id)
            .where(OrganizationAgent.agent_id == agent_id)
        )
        return session.exec(query).first()

    def deploy_agent(
        self,
        session: Session,
        org_id: str,
        agent_id: str,
        config: Dict[str, Any],
        deployed_by: str,
        enable_tasks: bool = True,
        enable_tools: bool = True,
    ) -> OrganizationAgent:
        """
        Deploy an agent for an organization.

        Args:
            session: Database session
            org_id: Organization ID
            agent_id: Agent ID
            config: Agent configuration
            deployed_by: User ID who deployed
            enable_tasks: Whether to enable scheduled tasks
            enable_tools: Whether to enable tool permissions

        Returns:
            OrganizationAgent object

        Raises:
            ValueError: If agent not found or deployment fails
        """
        # Get agent
        agent = session.get(Agent, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Get or create organization agent
        org_agent = self.get_organization_agent(session, org_id, agent_id)
        if not org_agent:
            org_agent = OrganizationAgent(
                id=str(uuid4()),
                org_id=org_id,
                agent_id=agent_id,
                agent_name=agent.name,
                status=AgentStatus.DISABLED,
                config=config,
            )
            session.add(org_agent)

        # Update configuration
        org_agent.config = config
        org_agent.deployed_by = deployed_by
        org_agent.deployed_at = datetime.utcnow()
        org_agent.last_error = None
        org_agent.error_at = None

        try:
            # Deploy scheduled tasks if enabled
            if enable_tasks and agent.default_tasks:
                self._deploy_tasks(session, org_id, agent, config)

            # Note: Tool permissions would be handled here
            # For now, we'll just mark it as deployed
            if enable_tools:
                # TODO: Implement tool permission setup
                logger.info(f"Tool permissions enabled for agent {agent.name} (org {org_id})")

            org_agent.status = AgentStatus.DEPLOYED
            session.commit()
            session.refresh(org_agent)

            logger.info(f"Deployed agent {agent.name} for organization {org_id}")
            return org_agent

        except Exception as e:
            org_agent.status = AgentStatus.ERROR
            org_agent.last_error = str(e)
            org_agent.error_at = datetime.utcnow()
            session.commit()
            logger.error(f"Error deploying agent {agent.name}: {e}")
            raise ValueError(f"Failed to deploy agent: {e}") from e

    def _deploy_tasks(
        self, session: Session, org_id: str, agent: Agent, config: Dict[str, Any]
    ):
        """
        Deploy scheduled tasks for an agent.

        Args:
            session: Database session
            org_id: Organization ID
            agent: Agent object
            config: Agent configuration
        """
        if not agent.default_tasks or "tasks" not in agent.default_tasks:
            return

        tasks_data = agent.default_tasks.get("tasks", [])
        for task_data in tasks_data:
            # Create task ID with org prefix for isolation
            task_id = f"{org_id}:{agent.name}:{task_data['name']}"

            # Check if task already exists
            existing_task = session.get(ScheduledTask, task_id)
            if existing_task:
                # Update existing task
                existing_task.enabled = task_data.get("enabled", True)
                existing_task.schedule = task_data["schedule"]
                existing_task.task_type = task_data.get("type", "cron")
                existing_task.function_path = task_data["function"]
                existing_task.args = task_data.get("args")
                # Merge config into kwargs
                kwargs = task_data.get("kwargs", {})
                kwargs.update(config)
                existing_task.kwargs = kwargs
            else:
                # Create new task
                scheduled_task = ScheduledTask(
                    id=task_id,
                    agent_name=f"{org_id}:{agent.name}",
                    task_name=task_data["name"],
                    description=task_data.get("description"),
                    enabled=task_data.get("enabled", True),
                    schedule=task_data["schedule"],
                    task_type=task_data.get("type", "cron"),
                    function_path=task_data["function"],
                    args=task_data.get("args"),
                    kwargs={**(task_data.get("kwargs", {})), **config},
                )
                session.add(scheduled_task)
                existing_task = scheduled_task

            session.commit()

            # Register with scheduler if enabled
            if existing_task.enabled:
                self.scheduler.register_task(existing_task)

    def update_agent_config(
        self,
        session: Session,
        org_id: str,
        agent_id: str,
        config: Dict[str, Any],
    ) -> OrganizationAgent:
        """
        Update agent configuration.

        Args:
            session: Database session
            org_id: Organization ID
            agent_id: Agent ID
            config: New configuration

        Returns:
            Updated OrganizationAgent object

        Raises:
            ValueError: If organization agent not found
        """
        org_agent = self.get_organization_agent(session, org_id, agent_id)
        if not org_agent:
            raise ValueError(f"Agent {agent_id} not deployed for organization {org_id}")

        org_agent.config = config
        session.commit()
        session.refresh(org_agent)

        # Update tasks with new config
        agent = session.get(Agent, agent_id)
        if agent and agent.default_tasks:
            self._deploy_tasks(session, org_id, agent, config)

        return org_agent

    def enable_agent(
        self, session: Session, org_id: str, agent_id: str
    ) -> OrganizationAgent:
        """
        Enable an agent for an organization.

        Args:
            session: Database session
            org_id: Organization ID
            agent_id: Agent ID

        Returns:
            Updated OrganizationAgent object

        Raises:
            ValueError: If organization agent not found
        """
        org_agent = self.get_organization_agent(session, org_id, agent_id)
        if not org_agent:
            raise ValueError(f"Agent {agent_id} not deployed for organization {org_id}")

        org_agent.status = AgentStatus.DEPLOYED
        session.commit()
        session.refresh(org_agent)

        # Enable tasks
        query = select(ScheduledTask).where(
            ScheduledTask.agent_name == f"{org_id}:{org_agent.agent_name}"
        )
        tasks = session.exec(query).all()
        for task in tasks:
            task.enabled = True
            self.scheduler.register_task(task)
        session.commit()

        return org_agent

    def disable_agent(
        self, session: Session, org_id: str, agent_id: str
    ) -> OrganizationAgent:
        """
        Disable an agent for an organization.

        Args:
            session: Database session
            org_id: Organization ID
            agent_id: Agent ID

        Returns:
            Updated OrganizationAgent object

        Raises:
            ValueError: If organization agent not found
        """
        org_agent = self.get_organization_agent(session, org_id, agent_id)
        if not org_agent:
            raise ValueError(f"Agent {agent_id} not deployed for organization {org_id}")

        org_agent.status = AgentStatus.DISABLED
        session.commit()
        session.refresh(org_agent)

        # Disable tasks
        query = select(ScheduledTask).where(
            ScheduledTask.agent_name == f"{org_id}:{org_agent.agent_name}"
        )
        tasks = session.exec(query).all()
        for task in tasks:
            task.enabled = False
            self.scheduler.unregister_task(task.id)
        session.commit()

        return org_agent
