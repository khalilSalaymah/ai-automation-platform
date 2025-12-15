"""Authentication and authorization utilities."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from enum import Enum

# Password hashing context
# Use pbkdf2_sha256 to avoid bcrypt backend/version issues and the 72-byte
# password limit while still providing a strong, salted hash.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def get_secret_key() -> str:
    """Get secret key from settings."""
    from .config import get_settings
    settings = get_settings()
    return settings.secret_key


class Role(str, Enum):
    """User roles."""

    ADMIN = "admin"
    CLIENT = "client"
    STAFF = "staff"


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""

    user_id: Optional[str] = None
    email: Optional[str] = None
    org_id: Optional[str] = None
    role: Optional[Role] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    secret_key = get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    secret_key = get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and verify a JWT token."""
    try:
        secret_key = get_secret_key()
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        org_id: str = payload.get("org_id")
        role: str = payload.get("role")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            org_id=org_id,
            role=Role(role) if role else None,
        )
    except JWTError:
        return None

