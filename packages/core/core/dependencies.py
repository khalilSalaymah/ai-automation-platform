"""FastAPI dependencies for authentication."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from .database import get_session
from .auth import decode_token, Role
from .models import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    token_data = decode_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(User, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(allowed_roles: list[Role]):
    """Dependency factory for role-based access control."""

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


# Common role dependencies
RequireAdmin = Depends(require_role([Role.ADMIN]))
RequireStaff = Depends(require_role([Role.ADMIN, Role.STAFF]))
RequireClient = Depends(require_role([Role.ADMIN, Role.STAFF, Role.CLIENT]))


async def get_user_org_id(current_user: User = Depends(get_current_active_user)) -> Optional[str]:
    """Get current user's organization ID."""
    return current_user.org_id




