"""Core package for AI agent framework."""

from .llm import LLM
from .memory import RedisSessionMemory
from .tools import Tool, ToolRegistry
from .embeddings import EmbeddingsStore
from .agents import BaseAgent, PlannerAgent, ToolExecutionAgent, AgentOrchestrator
from .logger import logger
from .config import get_env, Settings
from .errors import (
    AgentFrameworkError,
    ConfigError,
    LLMError,
    MemoryError,
    ToolError,
)
from .auth import Role, Token, TokenData, verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from .models import User, UserBase, UserCreate, UserUpdate, UserResponse, Organization
from .database import get_session, init_db, engine
from .dependencies import get_current_user, get_current_active_user, require_role, RequireAdmin, RequireStaff, RequireClient, get_user_org_id
from .auth_router import router as auth_router
from .billing_router import router as billing_router
from .billing_service import BillingService
from .billing_models import (
    Subscription,
    Quota,
    Usage,
    Invoice,
    SubscriptionStatus,
    UsageType,
    SubscriptionResponse,
    QuotaResponse,
    UsageResponse,
    UsageSummary,
    InvoiceResponse,
)
from .scheduler_models import (
    ScheduledTask,
    TaskExecution,
    TaskStatus,
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    TaskExecutionResponse,
    EventMessage,
)
from .scheduler import TaskScheduler
from .task_queue import TaskQueue
from .event_bus import EventBus
from .scheduler_router import router as scheduler_router
from .worker import create_worker
from .log_models import LogEntry, LogEntryResponse, LogQueryParams
from .log_router import router as log_router
from .observability import send_slack_alert, log_error_with_alert
from .knowledge_models import (
    Document,
    DocumentChunk,
    AgentDocument,
    DocumentSource,
    DocumentStatus,
    DocumentCreate,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    AgentDocumentLink,
    AgentDocumentResponse,
)
from .knowledge_service import KnowledgeBaseService, DocumentChunker
from .url_crawler import URLCrawler
from .notion_importer import NotionImporter
from .knowledge_router import router as knowledge_router
from .agent_marketplace_models import (
    Agent,
    OrganizationAgent,
    AgentStatus,
    AgentResponse,
    OrganizationAgentResponse,
    AgentConfigUpdate,
    AgentDeployRequest,
    AgentEnableRequest,
)
from .agent_marketplace_service import AgentMarketplaceService
from .agent_marketplace_router import router as agent_marketplace_router

__all__ = [
    "LLM",
    "RedisSessionMemory",
    "Tool",
    "ToolRegistry",
    "EmbeddingsStore",
    "BaseAgent",
    "PlannerAgent",
    "ToolExecutionAgent",
    "AgentOrchestrator",
    "logger",
    "get_env",
    "Settings",
    "AgentFrameworkError",
    "ConfigError",
    "LLMError",
    "MemoryError",
    "ToolError",
    # Auth exports
    "Role",
    "Token",
    "TokenData",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "User",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Organization",
    "get_session",
    "init_db",
    "engine",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "RequireAdmin",
    "RequireStaff",
    "RequireClient",
    "get_user_org_id",
    "auth_router",
    "billing_router",
    "BillingService",
    "Subscription",
    "Quota",
    "Usage",
    "Invoice",
    "SubscriptionStatus",
    "UsageType",
    "SubscriptionResponse",
    "QuotaResponse",
    "UsageResponse",
    "UsageSummary",
    "InvoiceResponse",
    # Scheduler exports
    "ScheduledTask",
    "TaskExecution",
    "TaskStatus",
    "ScheduledTaskCreate",
    "ScheduledTaskResponse",
    "TaskExecutionResponse",
    "EventMessage",
    "TaskScheduler",
    "TaskQueue",
    "EventBus",
    "scheduler_router",
    "create_worker",
    # Log exports
    "LogEntry",
    "LogEntryResponse",
    "LogQueryParams",
    "log_router",
    # Observability exports
    "send_slack_alert",
    "log_error_with_alert",
    # Knowledge base exports
    "Document",
    "DocumentChunk",
    "AgentDocument",
    "DocumentSource",
    "DocumentStatus",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentSearchRequest",
    "DocumentSearchResult",
    "AgentDocumentLink",
    "AgentDocumentResponse",
    "KnowledgeBaseService",
    "DocumentChunker",
    "URLCrawler",
    "NotionImporter",
    "knowledge_router",
    # Agent marketplace exports
    "Agent",
    "OrganizationAgent",
    "AgentStatus",
    "AgentResponse",
    "OrganizationAgentResponse",
    "AgentConfigUpdate",
    "AgentDeployRequest",
    "AgentEnableRequest",
    "AgentMarketplaceService",
    "agent_marketplace_router",
]

