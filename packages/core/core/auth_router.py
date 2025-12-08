"""Authentication router for FastAPI."""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse

from .database import get_session
from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    Token,
    Role,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .models import User, UserCreate, UserResponse
from .dependencies import get_current_active_user
from .config import get_settings

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str

# OAuth2 Google configuration
config = Config()
oauth = OAuth(config)

# Google OAuth (configure via environment variables)
GOOGLE_CLIENT_ID = getattr(settings, "google_client_id", None)
GOOGLE_CLIENT_SECRET = getattr(settings, "google_client_secret", None)
GOOGLE_REDIRECT_URI = getattr(settings, "google_redirect_uri", "http://localhost:8000/api/auth/google/callback")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: Session = Depends(get_session),
):
    """Register a new user."""
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = None
    if user_data.password:
        hashed_password = get_password_hash(user_data.password)

    import uuid

    new_user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        org_id=user_data.org_id,
        is_active=True,
        is_verified=False,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
):
    """Login with email and password."""
    user = session.exec(select(User).where(User.email == login_data.email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password not set. Please use OAuth login.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user.id,
        "email": user.email,
        "org_id": user.org_id,
        "role": user.role.value,
    }

    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """Refresh access token using refresh token."""
    token_data = decode_token(request.refresh_token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = session.get(User, token_data.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token_data = {
        "sub": user.id,
        "email": user.email,
        "org_id": user.org_id,
        "role": user.role.value,
    }

    access_token = create_access_token(data=new_token_data, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data=new_token_data)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""

    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """Request password reset (placeholder - implement email sending)."""
    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If email exists, password reset link has been sent"}

    # TODO: Implement email sending with reset token
    # For now, just return success
    return {"message": "If email exists, password reset link has been sent"}


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""

    token: str
    new_password: str


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """Reset password with token."""
    # TODO: Implement token validation and password reset
    # For now, placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented",
    )


# Google OAuth routes
@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    session: Session = Depends(get_session),
):
    """Handle Google OAuth callback."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google",
            )

        email = user_info.get("email")
        google_id = user_info.get("sub")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")

        # Check if user exists
        user = session.exec(select(User).where(User.email == email)).first()

        if not user:
            # Create new user
            import uuid

            user = User(
                id=str(uuid.uuid4()),
                email=email,
                full_name=full_name,
                google_id=google_id,
                avatar_url=avatar_url,
                is_active=True,
                is_verified=True,  # Google verified
                role=Role.CLIENT,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Update existing user
            user.google_id = google_id
            user.avatar_url = avatar_url
            user.is_verified = True
            if full_name:
                user.full_name = full_name
            session.add(user)
            session.commit()

        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user.id,
            "email": user.email,
            "org_id": user.org_id,
            "role": user.role.value,
        }

        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data=token_data)

        # Redirect to frontend with tokens
        frontend_url = getattr(settings, "frontend_url", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {str(e)}",
        )

