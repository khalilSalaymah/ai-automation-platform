"""Agent marketplace models and schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum as PyEnum
from sqlmodel import SQLModel, Field, Column, String, JSON, Text
from sqlalchemy import DateTime, func


class AgentStatus(str, PyEnum):
    """Agent deployment status."""

    AVAILABLE = "available"
    DEPLOYED = "deployed"
    DISABLED = "disabled"
    ERROR = "error"


class Agent(SQLModel, table=True):
    """Agent definition in marketplace."""

    __tablename__ = "agents"

    id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # e.g., "email-agent", "aiops-bot"
    display_name: str
    description: str = Field(sa_column=Column(Text))
    version: str = Field(default="1.0.0")
    category: Optional[str] = None  # e.g., "automation", "monitoring", "support"
    icon_url: Optional[str] = None
    author: Optional[str] = None
    
    # Agent configuration schema (JSON Schema format)
    config_schema: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Required tools/permissions
    required_tools: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # Default scheduled tasks (YAML-like structure)
    default_tasks: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Metadata
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    documentation_url: Optional[str] = None
    
    # Status
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class OrganizationAgent(SQLModel, table=True):
    """Organization-specific agent deployment."""

    __tablename__ = "organization_agents"

    id: Optional[str] = Field(default=None, primary_key=True)
    org_id: str = Field(index=True)
    agent_id: str = Field(index=True)
    agent_name: str = Field(index=True)  # Denormalized for easier queries
    
    # Deployment status
    status: AgentStatus = Field(default=AgentStatus.DISABLED, index=True)
    
    # Configuration (JSON matching agent's config_schema)
    config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Deployment metadata
    deployed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    deployed_by: Optional[str] = None  # User ID
    
    # Error tracking
    last_error: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


# Request/Response models
class AgentResponse(SQLModel):
    """Agent response model."""

    id: str
    name: str
    display_name: str
    description: str
    version: str
    category: Optional[str]
    icon_url: Optional[str]
    author: Optional[str]
    config_schema: Dict[str, Any]
    required_tools: List[str]
    default_tasks: Optional[Dict[str, Any]]
    tags: List[str]
    documentation_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationAgentResponse(SQLModel):
    """Organization agent response model."""

    id: str
    org_id: str
    agent_id: str
    agent_name: str
    status: AgentStatus
    config: Dict[str, Any]
    deployed_at: Optional[datetime]
    deployed_by: Optional[str]
    last_error: Optional[str]
    error_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Include agent details
    agent: Optional[AgentResponse] = None


class AgentConfigUpdate(SQLModel):
    """Update agent configuration."""

    config: Dict[str, Any]


class AgentDeployRequest(SQLModel):
    """Deploy agent request."""

    config: Dict[str, Any]
    enable_tasks: bool = True
    enable_tools: bool = True


class AgentEnableRequest(SQLModel):
    """Enable/disable agent request."""

    enabled: bool
