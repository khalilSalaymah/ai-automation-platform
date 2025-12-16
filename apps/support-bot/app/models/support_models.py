"""Support bot domain models."""

from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Supported customer intent labels."""

    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class SupportChatRequest(BaseModel):
    """Chat request from the client."""

    message: str = Field(..., description="User message")
    session_id: str = Field("default", description="Conversation session identifier")
    user_id: Optional[str] = Field(
        default=None, description="Optional authenticated user identifier"
    )


class SupportChatResponse(BaseModel):
    """Structured chat response with intent and escalation metadata."""

    response: str = Field(..., description="Bot answer presented to the user")
    intent: Intent = Field(..., description="Classified user intent")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score combining retrieval and self-evaluation",
    )
    escalated: bool = Field(
        ...,
        description="Whether the conversation has been escalated to a human agent",
    )
    ticket_id: Optional[str] = Field(
        default=None,
        description="Support ticket identifier when escalation occurs",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="RAG document sources used for the answer",
    )


class TicketPriority(str, Enum):
    """Ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TicketStatus(str, Enum):
    """Ticket lifecycle status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class CreateTicketRequest(BaseModel):
    """Request payload to create a support ticket."""

    subject: str
    description: str
    intent: Optional[Intent] = None
    priority: TicketPriority = TicketPriority.MEDIUM
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class Ticket(BaseModel):
    """Support ticket representation."""

    id: str
    subject: str
    description: str
    intent: Optional[Intent] = None
    priority: TicketPriority
    status: TicketStatus
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class TicketStatusResponse(BaseModel):
    """Response model for ticket status queries."""

    ticket: Optional[Ticket] = None
    found: bool = True

