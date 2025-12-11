"""Database models for integration tokens."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import DateTime, func, Text
import uuid
try:
    from cryptography.fernet import Fernet
except ImportError:
    # Fallback if cryptography is not installed
    Fernet = None
import base64
import os


def get_encryption_key() -> bytes:
    """Get or generate encryption key for tokens."""
    if Fernet is None:
        raise ImportError("cryptography package is required for token encryption. Install it with: pip install cryptography")
    
    key = os.getenv("INTEGRATION_ENCRYPTION_KEY")
    if not key:
        # Generate a key if not set (should be set in production!)
        key = Fernet.generate_key().decode()
        print(f"WARNING: Generated encryption key. Set INTEGRATION_ENCRYPTION_KEY={key} in .env")
    else:
        key = key.encode() if isinstance(key, str) else key
    return key


class IntegrationToken(SQLModel, table=True):
    """Encrypted storage for OAuth tokens."""

    __tablename__ = "integration_tokens"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    org_id: Optional[str] = Field(default=None, index=True)
    integration_name: str = Field(index=True)  # e.g., "slack", "gmail", etc.
    encrypted_token: str = Field(sa_column=Column(Text))  # Encrypted OAuth token
    encrypted_refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    expires_at: Optional[datetime] = None
    metadata: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON string for additional data
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        key = get_encryption_key()
        f = Fernet(key)
        return f.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token."""
        key = get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_token.encode()).decode()

    def set_token(self, token: str, refresh_token: Optional[str] = None):
        """Set and encrypt tokens."""
        self.encrypted_token = self.encrypt_token(token)
        if refresh_token:
            self.encrypted_refresh_token = self.encrypt_token(refresh_token)

    def get_token(self) -> str:
        """Get and decrypt token."""
        return self.decrypt_token(self.encrypted_token)

    def get_refresh_token(self) -> Optional[str]:
        """Get and decrypt refresh token."""
        if self.encrypted_refresh_token:
            return self.decrypt_token(self.encrypted_refresh_token)
        return None
