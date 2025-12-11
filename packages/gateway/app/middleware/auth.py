"""JWT authentication middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth import decode_token, TokenData
from core.logger import logger

security = HTTPBearer(auto_error=False)


async def verify_token(request: Request) -> Optional[TokenData]:
    """
    Verify JWT token from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        TokenData if valid, None otherwise
    """
    # Try to get token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    # Decode and verify token
    token_data = decode_token(token)
    if token_data is None:
        logger.warning(f"Invalid token for request to {request.url.path}")
        return None
    
    return token_data


async def get_current_user_token(request: Request) -> TokenData:
    """
    Get current user token data from request.
    Raises HTTPException if token is invalid or missing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        TokenData object
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token_data = await verify_token(request)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data
