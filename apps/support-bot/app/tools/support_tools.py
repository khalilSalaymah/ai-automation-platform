"""Support bot tools for ticketing.

These provide a mock ticketing system implemented on top of Redis so the
application can run locally without any external dependencies.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

import redis
from loguru import logger

from core.tools import Tool, ToolRegistry

from ..config import settings
from ..models.support_models import Ticket, TicketPriority, TicketStatus


def _get_redis_client() -> redis.Redis:
    """Create a Redis client for ticket storage."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


class CreateTicketTool(Tool):
    """Create a support ticket in the mock ticketing system."""

    def __init__(self) -> None:
        super().__init__(
            name="create_support_ticket",
            description=(
                "Create a support ticket when the AI is not confident enough. "
                "Use this when the confidence is below the escalation threshold."
            ),
        )

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create and persist a ticket."""
        r = _get_redis_client()

        subject: str = inputs.get("subject") or "Support request"
        description: str = inputs.get("description") or ""
        intent: str = (inputs.get("intent") or "general").lower()
        priority_str: str = (inputs.get("priority") or TicketPriority.MEDIUM.value).lower()
        session_id: str = inputs.get("session_id") or "default"
        user_id: str | None = inputs.get("user_id")

        ticket_id = inputs.get("ticket_id") or str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        try:
            priority = TicketPriority(priority_str)
        except ValueError:
            priority = TicketPriority.MEDIUM

        ticket = Ticket(
            id=ticket_id,
            subject=subject,
            description=description,
            intent=intent,  # type: ignore[arg-type]
            priority=priority,
            status=TicketStatus.OPEN,
            session_id=session_id,
            user_id=user_id,
        )

        key = f"ticket:{ticket_id}"
        logger.info(f"Creating support ticket {ticket_id} with priority={priority.value}")
        r.hset(
            key,
            mapping={
                "subject": ticket.subject,
                "description": ticket.description,
                "intent": ticket.intent.value if ticket.intent else "",
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "session_id": ticket.session_id or "",
                "user_id": ticket.user_id or "",
                "created_at": created_at,
            },
        )

        return {
            "ticket_id": ticket_id,
            "status": ticket.status.value,
            "priority": ticket.priority.value,
        }

    def to_function_schema(self) -> Dict[str, Any]:
        """Tool schema for LLM function-calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "description": {"type": "string"},
                        "intent": {
                            "type": "string",
                            "enum": ["billing", "technical", "general"],
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "session_id": {"type": "string"},
                        "user_id": {"type": "string"},
                    },
                    "required": ["description"],
                },
            },
        }


class GetTicketStatusTool(Tool):
    """Retrieve status for an existing ticket."""

    def __init__(self) -> None:
        super().__init__(
            name="get_ticket_status",
            description="Get the current status and details of a support ticket.",
        )

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticket_id: str | None = inputs.get("ticket_id")
        if not ticket_id:
            return {"success": False, "error": "ticket_id is required"}

        r = _get_redis_client()
        key = f"ticket:{ticket_id}"
        data = r.hgetall(key)

        if not data:
            logger.warning(f"Ticket {ticket_id} not found in mock store")
            return {"success": False, "error": "Ticket not found"}

        logger.info(f"Loaded ticket {ticket_id} with status={data.get('status')}")
        return {
            "success": True,
            "ticket_id": ticket_id,
            "status": data.get("status", TicketStatus.OPEN.value),
            "priority": data.get("priority", TicketPriority.MEDIUM.value),
            "subject": data.get("subject", ""),
            "description": data.get("description", ""),
            "intent": data.get("intent", ""),
            "session_id": data.get("session_id", ""),
            "user_id": data.get("user_id", ""),
        }

    def to_function_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                    },
                    "required": ["ticket_id"],
                },
            },
        }


class SupportTools:
    """Helper to register all support-bot specific tools."""

    def register_all(self, registry: ToolRegistry) -> None:
        registry.register(CreateTicketTool())
        registry.register(GetTicketStatusTool())


