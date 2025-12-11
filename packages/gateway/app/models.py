"""Gateway models."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class GatewayRequest(BaseModel):
    """Gateway request model."""

    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Any] = None
    query_params: Optional[Dict[str, str]] = None


class GatewayResponse(BaseModel):
    """Gateway response model."""

    status_code: int
    headers: Dict[str, str]
    body: Any


class RequestLog(BaseModel):
    """Request log model."""

    user_id: Optional[str] = None
    method: str
    path: str
    agent: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error: Optional[str] = None
