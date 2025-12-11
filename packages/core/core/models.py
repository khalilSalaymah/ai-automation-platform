"""Database models for authentication."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON
from sqlalchemy import DateTime, func
from enum import Enum as PyEnum
from .auth import Role


class UserBase(SQLModel):
    """Base user model."""

    email: str = Field(unique=True, index=True, sa_column=Column(String, unique=True, index=True))
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    role: Role = Field(default=Role.CLIENT)
    org_id: Optional[str] = Field(default=None, index=True)  # Multi-tenant support
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    avatar_url: Optional[str] = None


class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    id: Optional[str] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = None  # None for OAuth users
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class UserCreate(SQLModel):
    """User creation model."""

    email: str
    password: Optional[str] = None
    full_name: Optional[str] = None
    org_id: Optional[str] = None
    role: Role = Role.CLIENT


class UserUpdate(SQLModel):
    """User update model."""

    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[Role] = None
    org_id: Optional[str] = None


class UserResponse(SQLModel):
    """User response model."""

    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: Role
    org_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime


class Organization(SQLModel, table=True):
    """Organization model for multi-tenancy."""

    __tablename__ = "organizations"

    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(unique=True, index=True)
    # White-label branding fields
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = Field(default=None, unique=True, index=True)
    theme_variables: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )



