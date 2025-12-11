"""Billing quota checking middleware."""

from fastapi import Request, HTTPException, status
from sqlmodel import Session, create_engine
from core.logger import logger
from core.billing_service import BillingService
from core.billing_models import UsageType
from core.config import get_settings as get_core_settings
from ..middleware.auth import verify_token
from ..config import get_settings

# Create database engine for quota checking
_core_settings = get_core_settings()
_engine = None


def get_db_engine():
    """Get database engine for quota checking."""
    global _engine
    if _engine is None:
        _engine = create_engine(_core_settings.database_url)
    return _engine


async def check_quota_middleware(request: Request, call_next):
    """
    Check billing quota before processing request.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response
    """
    # Skip quota checking for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get user ID from token
    token_data = await verify_token(request)
    if not token_data:
        # If no token, let auth middleware handle it
        return await call_next(request)
    
    user_id = token_data.user_id
    
    # Determine usage type based on agent
    agent = _get_agent_from_path(request.url.path)
    if agent:
        usage_type = _get_usage_type_for_agent(agent)
        
        # Get database session
        engine = get_db_engine()
        with Session(engine) as session:
            try:
                # Check quota
                is_allowed, error_msg = BillingService.check_quota(
                    session=session,
                    user_id=user_id,
                    usage_type=usage_type,
                    requested_quantity=1,
                )
                
                if not is_allowed:
                    logger.warning(f"Quota exceeded for user {user_id}: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=error_msg,
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking quota: {e}")
                # Don't block request if quota check fails
                pass
    
    response = await call_next(request)
    return response


def _get_agent_from_path(path: str) -> str:
    """Extract agent name from path."""
    # Path format: /api/{agent}/...
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return ""


def _get_usage_type_for_agent(agent: str) -> UsageType:
    """Map agent name to usage type."""
    agent_usage_map = {
        "email": UsageType.API_CALLS,
        "rag": UsageType.API_CALLS,
        "scraper": UsageType.SCRAPING_TASKS,
        "support": UsageType.API_CALLS,
        "aiops": UsageType.API_CALLS,
    }
    return agent_usage_map.get(agent, UsageType.API_CALLS)
