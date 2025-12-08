"""Email data models."""

from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailRequest(BaseModel):
    """Email processing request."""

    email: str
    subject: str
    from_email: EmailStr
    session_id: Optional[str] = None


class EmailResponse(BaseModel):
    """Email processing response."""

    response: str
    category: str = "general"
    priority: str = "normal"
    suggested_action: str = "read"


class EmailHistory(BaseModel):
    """Email history record."""

    id: str
    subject: str
    from_email: str
    category: str
    priority: str
    processed_at: str

