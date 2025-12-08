"""Support models."""

from pydantic import BaseModel


class SupportRequest(BaseModel):
    message: str
    session_id: str = "default"


class SupportResponse(BaseModel):
    response: str

