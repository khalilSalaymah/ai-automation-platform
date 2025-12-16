"""Support API routes."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from core.logger import logger

from ..models.support_models import (
    CreateTicketRequest,
    SupportChatRequest,
    SupportChatResponse,
    Ticket,
    TicketStatusResponse,
)
from ..services.support_service import SupportService

router = APIRouter()


@router.post("/chat", response_model=SupportChatResponse)
async def chat(request: SupportChatRequest) -> SupportChatResponse:
    """Chat with the support bot over HTTP."""
    try:
        service = SupportService()
        return await service.chat(request)
    except Exception as exc:
        logger.error(f"Error in /chat: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/tickets", response_model=Ticket)
async def create_ticket(request: CreateTicketRequest) -> Ticket:
    """Explicitly create a support ticket via API."""
    try:
        service = SupportService()
        return await service.create_ticket(request)
    except Exception as exc:
        logger.error(f"Error creating ticket: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tickets/{ticket_id}", response_model=TicketStatusResponse)
async def get_ticket(ticket_id: str) -> TicketStatusResponse:
    """Get ticket status and details."""
    try:
        service = SupportService()
        return await service.get_ticket(ticket_id)
    except Exception as exc:
        logger.error(f"Error getting ticket {ticket_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.websocket("/ws")
async def websocket_chat(ws: WebSocket) -> None:
    """WebSocket chat endpoint.

    Protocol:
    - Client sends: {"message": "text", "session_id": "optional"}
    - Server responds with SupportChatResponse JSON.
    """
    await ws.accept()
    service = SupportService()

    try:
        while True:
            data = await ws.receive_json()
            message: str = data.get("message", "") or ""
            session_id: str = data.get("session_id") or "default"

            logger.info(f"WebSocket message for session={session_id}")

            req = SupportChatRequest(message=message, session_id=session_id)
            resp = await service.chat(req)

            await ws.send_json(resp.model_dump())
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for support-bot")
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}", exc_info=True)
        try:
            await ws.send_json({"error": str(exc)})
        except Exception:
            # Socket may already be closed
            pass

