"""Email API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.logger import logger

from ..services.email_service import EmailService
from ..models.email_models import EmailRequest, EmailResponse, EmailHistory

router = APIRouter()


@router.post("/process", response_model=EmailResponse)
async def process_email(request: EmailRequest):
    """Process an incoming email."""
    try:
        service = EmailService()
        result = await service.process_email(request)
        return result
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond", response_model=EmailResponse)
async def generate_response(request: EmailRequest):
    """Generate an email response."""
    try:
        service = EmailService()
        result = await service.generate_response(request)
        return result
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[EmailHistory])
async def get_history(limit: int = 10, offset: int = 0):
    """Get email history."""
    try:
        service = EmailService()
        history = await service.get_history(limit=limit, offset=offset)
        return history
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

