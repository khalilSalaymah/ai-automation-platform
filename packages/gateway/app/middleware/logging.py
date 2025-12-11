"""Request logging middleware."""

import time
from datetime import datetime
from fastapi import Request
from core.logger import logger
from ..middleware.auth import verify_token
from ..models import RequestLog


async def logging_middleware(request: Request, call_next):
    """
    Log every request.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response
    """
    start_time = time.time()
    
    # Get user info
    token_data = await verify_token(request)
    user_id = token_data.user_id if token_data else None
    
    # Get agent from path
    agent = _get_agent_from_path(request.url.path)
    
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    error = None
    status_code = 200
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        error = str(e)
        status_code = 500
        raise
    finally:
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log request
        log_entry = RequestLog(
            user_id=user_id,
            method=request.method,
            path=str(request.url.path),
            agent=agent or "unknown",
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            error=error,
        )
        
        # Log to logger
        log_level = "error" if error else ("warning" if status_code >= 400 else "info")
        log_message = (
            f"Request: {request.method} {request.url.path} | "
            f"User: {user_id} | Agent: {agent} | "
            f"Status: {status_code} | Time: {response_time_ms:.2f}ms"
        )
        
        if error:
            logger.error(f"{log_message} | Error: {error}")
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)


def _get_agent_from_path(path: str) -> str:
    """Extract agent name from path."""
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return ""
