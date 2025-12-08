"""Usage metering utilities for tracking tokens, API calls, and scraping tasks."""

from typing import Optional
from sqlmodel import Session
from .billing_service import BillingService
from .billing_models import UsageType


def record_token_usage(
    session: Session,
    user_id: str,
    tokens: int,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Record token usage for a user.
    
    Args:
        session: Database session
        user_id: User ID
        tokens: Number of tokens used
        metadata: Optional metadata (e.g., model name, prompt type)
    
    Returns:
        True if usage was recorded successfully
    """
    try:
        BillingService.record_usage(
            session=session,
            user_id=user_id,
            usage_type=UsageType.TOKENS,
            quantity=tokens,
            metadata=metadata,
        )
        return True
    except Exception as e:
        print(f"Error recording token usage: {str(e)}")
        return False


def record_api_call_usage(
    session: Session,
    user_id: str,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Record API call usage for a user.
    
    Args:
        session: Database session
        user_id: User ID
        metadata: Optional metadata (e.g., endpoint, method)
    
    Returns:
        True if usage was recorded successfully
    """
    try:
        BillingService.record_usage(
            session=session,
            user_id=user_id,
            usage_type=UsageType.API_CALLS,
            quantity=1,
            metadata=metadata,
        )
        return True
    except Exception as e:
        print(f"Error recording API call usage: {str(e)}")
        return False


def record_scraping_task_usage(
    session: Session,
    user_id: str,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Record scraping task usage for a user.
    
    Args:
        session: Database session
        user_id: User ID
        metadata: Optional metadata (e.g., URL, pages scraped)
    
    Returns:
        True if usage was recorded successfully
    """
    try:
        BillingService.record_usage(
            session=session,
            user_id=user_id,
            usage_type=UsageType.SCRAPING_TASKS,
            quantity=1,
            metadata=metadata,
        )
        return True
    except Exception as e:
        print(f"Error recording scraping task usage: {str(e)}")
        return False


def check_token_quota(
    session: Session,
    user_id: str,
    requested_tokens: int = 1,
) -> tuple:
    """
    Check if user has token quota available.
    
    Args:
        session: Database session
        user_id: User ID
        requested_tokens: Number of tokens requested
    
    Returns:
        Tuple of (is_allowed, error_message)
    """
    return BillingService.check_quota(
        session=session,
        user_id=user_id,
        usage_type=UsageType.TOKENS,
        requested_quantity=requested_tokens,
    )


def check_api_call_quota(
    session: Session,
    user_id: str,
) -> tuple:
    """
    Check if user has API call quota available.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        Tuple of (is_allowed, error_message)
    """
    return BillingService.check_quota(
        session=session,
        user_id=user_id,
        usage_type=UsageType.API_CALLS,
        requested_quantity=1,
    )


def check_scraping_task_quota(
    session: Session,
    user_id: str,
) -> tuple:
    """
    Check if user has scraping task quota available.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        Tuple of (is_allowed, error_message)
    """
    return BillingService.check_quota(
        session=session,
        user_id=user_id,
        usage_type=UsageType.SCRAPING_TASKS,
        requested_quantity=1,
    )
