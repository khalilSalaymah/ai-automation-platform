"""Support bot service layer.

This module wires together:
- Core LLM wrapper
- Redis session memory
- PGVector-based RAG for answer generation
- SupportAgent orchestrator (intent → answer → escalation)
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from loguru import logger

from core import LLM, RedisSessionMemory, EmbeddingGenerator
from core.tools import ToolRegistry
from core.vectorstore import PGVectorStore

from ..agents.support_agent import SupportAgent, simple_intent_classifier
from ..config import settings
from ..models.support_models import (
    CreateTicketRequest,
    Intent,
    SupportChatRequest,
    SupportChatResponse,
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketStatusResponse,
)
from ..tools.support_tools import SupportTools


def compute_confidence(
    retrieval_confidence: float,
    self_eval_confidence: float,
) -> float:
    """Combine retrieval and self-evaluation confidences into a single score."""
    retrieval_confidence = max(0.0, min(1.0, retrieval_confidence))
    self_eval_confidence = max(0.0, min(1.0, self_eval_confidence))
    return (retrieval_confidence + self_eval_confidence) / 2.0


def should_escalate(confidence: float, threshold: float = 0.65) -> bool:
    """Return True when conversation should be escalated."""
    return confidence < threshold


class SupportService:
    """Facade for all support-bot domain operations."""

    def __init__(self) -> None:
        # LLM will auto-detect provider from LLM_PROVIDER env var.
        # Groq with an open model is the default in this monorepo.
        self.llm = LLM()
        self.memory = RedisSessionMemory(url=settings.redis_url)
        self.embedding_gen = EmbeddingGenerator()

        # Reuse existing PGVector pattern; we target the same table as rag-chat
        # so both apps can share knowledge documents.
        self.vector_store = PGVectorStore(
            uri=settings.database_url,
            table_name="rag_documents",
        )

        self.tools = ToolRegistry()
        SupportTools().register_all(self.tools)

        self.agent = SupportAgent(
            name="support-agent",
            llm=self.llm,
            memory=self.memory,
            vector_store=self.vector_store,
            embedding_gen=self.embedding_gen,
            tools=self.tools,
            escalation_threshold=0.65,
        )

    async def chat(self, request: SupportChatRequest) -> SupportChatResponse:
        """Run the full support pipeline for a single message."""
        logger.info(
            f"SupportService.chat: session_id={request.session_id}, "
            f"user_id={request.user_id}"
        )

        result = self.agent.act(
            {
                "query": request.message,
                "session_id": request.session_id,
                "user_id": request.user_id,
            }
        )

        return SupportChatResponse(
            response=result.get("response", ""),
            intent=Intent(result.get("intent", Intent.GENERAL.value)),
            confidence=float(result.get("confidence", 0.0)),
            escalated=bool(result.get("escalated", False)),
            ticket_id=result.get("ticket_id"),
            sources=result.get("sources", []),
        )

    async def handle_message(self, message: str, session_id: str):
        """Backward-compatible wrapper used by older callers."""
        req = SupportChatRequest(message=message, session_id=session_id)
        resp = await self.chat(req)
        return resp.model_dump()

    async def create_ticket(self, req: CreateTicketRequest) -> Ticket:
        """Create a support ticket via the ticketing tools."""
        intent = req.intent or simple_intent_classifier(req.description)

        payload = {
            "subject": req.subject,
            "description": req.description,
            "intent": intent.value,
            "priority": req.priority.value,
            "session_id": req.session_id or "default",
            "user_id": req.user_id,
        }

        logger.info(
            f"Creating ticket from API: subject='{req.subject[:40]}', "
            f"intent={intent.value}, priority={req.priority.value}"
        )

        result = self.tools.execute("create_support_ticket", payload)
        ticket_id = result.get("ticket_id")

        return Ticket(
            id=ticket_id,
            subject=req.subject,
            description=req.description,
            intent=intent,
            priority=req.priority,
            status=TicketStatus.OPEN,
            session_id=req.session_id,
            user_id=req.user_id,
        )

    async def get_ticket(self, ticket_id: str) -> TicketStatusResponse:
        """Return the current status of a ticket."""
        result = self.tools.execute("get_ticket_status", {"ticket_id": ticket_id})

        if not result.get("success"):
            return TicketStatusResponse(ticket=None, found=False)

        ticket = Ticket(
            id=ticket_id,
            subject=result.get("subject", ""),
            description=result.get("description", ""),
            intent=Intent(result.get("intent", Intent.GENERAL.value))
            if result.get("intent")
            else None,
            priority=TicketPriority(result.get("priority", TicketPriority.MEDIUM.value)),
            status=TicketStatus(result.get("status", TicketStatus.OPEN.value)),
            session_id=result.get("session_id") or None,
            user_id=result.get("user_id") or None,
        )

        return TicketStatusResponse(ticket=ticket, found=True)

