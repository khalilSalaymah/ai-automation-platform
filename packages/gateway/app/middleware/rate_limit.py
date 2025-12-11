"""Rate limiting middleware."""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException, status
from core.logger import logger
from ..config import get_settings

settings = get_settings()

# In-memory rate limit storage (use Redis in production)
_rate_limit_store: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))


def check_rate_limit(user_id: str, limit_per_minute: int, limit_per_hour: int) -> tuple[bool, Optional[str]]:
    """
    Check if user has exceeded rate limits.
    
    Args:
        user_id: User ID
        limit_per_minute: Requests per minute limit
        limit_per_hour: Requests per hour limit
        
    Returns:
        Tuple of (is_allowed, error_message)
    """
    now = datetime.utcnow()
    user_requests = _rate_limit_store[user_id]
    
    # Clean old requests
    minute_ago = now - timedelta(minutes=1)
    hour_ago = now - timedelta(hours=1)
    
    user_requests["minute"] = [ts for ts in user_requests["minute"] if ts > minute_ago]
    user_requests["hour"] = [ts for ts in user_requests["hour"] if ts > hour_ago]
    
    # Check minute limit
    if len(user_requests["minute"]) >= limit_per_minute:
        return False, f"Rate limit exceeded: {limit_per_minute} requests per minute"
    
    # Check hour limit
    if len(user_requests["hour"]) >= limit_per_hour:
        return False, f"Rate limit exceeded: {limit_per_hour} requests per hour"
    
    # Record request
    user_requests["minute"].append(now)
    user_requests["hour"].append(now)
    
    return True, None


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response
    """
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get user ID from token (if available)
    from .auth import verify_token
    token_data = await verify_token(request)
    user_id = token_data.user_id if token_data else request.client.host
    
    # Check rate limit
    is_allowed, error_msg = check_rate_limit(
        user_id=user_id,
        limit_per_minute=settings.rate_limit_per_minute,
        limit_per_hour=settings.rate_limit_per_hour,
    )
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {user_id}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg,
        )
    
    response = await call_next(request)
    return response
