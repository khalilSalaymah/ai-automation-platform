"""Support API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.logger import logger
from ..services.support_service import SupportService

router = APIRouter()


class SupportRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
async def chat(request: SupportRequest):
    try:
        service = SupportService()
        result = await service.handle_message(request.message, request.session_id)
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

