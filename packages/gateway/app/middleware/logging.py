"""Request logging middleware with trace_id support."""

import time
from datetime import datetime
from fastapi import Request, Response
from core.logger import (
    logger,
    generate_trace_id,
    set_trace_id,
    get_trace_id,
    generate_span_id,
    set_span_id,
    log_span,
)
from core.observability import log_error_with_alert
from ..middleware.auth import verify_token
from ..models import RequestLog


async def logging_middleware(request: Request, call_next):
    """
    Log every request with trace_id and span tracking.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response
    """
    start_time = time.time()
    
    # Generate or extract trace_id from headers
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    set_trace_id(trace_id)
    
    # Generate span_id for this request
    span_id = generate_span_id()
    set_span_id(span_id)
    
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
    
    # Log request start
    logger.info(
        "Request started",
        method=request.method,
        path=str(request.url.path),
        user_id=user_id,
        agent=agent,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Add trace_id to response headers
        # Note: FastAPI responses may be different types, so we try to add the header
        try:
            if hasattr(response, "headers"):
                response.headers["X-Trace-ID"] = trace_id
        except Exception:
            # If we can't add headers, that's okay
            pass
            
        return response
    except Exception as e:
        error = str(e)
        status_code = 500
        
        # Log error with alert
        log_error_with_alert(
            message=f"Request failed: {request.method} {request.url.path}",
            error=e,
            metadata={
                "method": request.method,
                "path": str(request.url.path),
                "user_id": user_id,
                "agent": agent,
                "status_code": status_code,
            },
        )
        raise
    finally:
        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Log request span
        log_span(
            operation="http_request",
            service="gateway",
            metadata={
                "method": request.method,
                "path": str(request.url.path),
                "user_id": user_id,
                "agent": agent or "unknown",
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "ip_address": ip_address,
            },
            start_time=start_time,
            end_time=end_time,
            error=error,
        )
        
        # Log request completion
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
