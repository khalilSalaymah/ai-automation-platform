"""Database models for billing and subscriptions."""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship, Column, String, Integer, Numeric, JSON
from sqlalchemy import DateTime, func, ForeignKey, Text
from enum import Enum as PyEnum


class SubscriptionStatus(str, PyEnum):
    """Subscription status enum."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class UsageType(str, PyEnum):
    """Usage type enum."""

    TOKENS = "tokens"
    API_CALLS = "api_calls"
    SCRAPING_TASKS = "scraping_tasks"


class Subscription(SQLModel, table=True):
    """Subscription database model."""

    __tablename__ = "subscriptions"

    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    stripe_subscription_id: str = Field(unique=True, index=True)
    stripe_customer_id: str = Field(index=True)
    stripe_price_id: Optional[str] = None
    status: SubscriptionStatus = Field(default=SubscriptionStatus.INCOMPLETE)
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class Quota(SQLModel, table=True):
    """Quota limits for subscriptions."""

    __tablename__ = "quotas"

    id: Optional[str] = Field(default=None, primary_key=True)
    subscription_id: str = Field(foreign_key="subscriptions.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    max_tokens: int = Field(default=0)  # 0 = unlimited
    max_api_calls: int = Field(default=0)  # 0 = unlimited
    max_scraping_tasks: int = Field(default=0)  # 0 = unlimited
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )


class Usage(SQLModel, table=True):
    """Usage tracking model."""

    __tablename__ = "usage"

    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    subscription_id: Optional[str] = Field(default=None, foreign_key="subscriptions.id", index=True)
    usage_type: UsageType
    quantity: int = Field(default=0)
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )


class Invoice(SQLModel, table=True):
    """Invoice database model."""

    __tablename__ = "invoices"

    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    subscription_id: Optional[str] = Field(default=None, foreign_key="subscriptions.id", index=True)
    stripe_invoice_id: str = Field(unique=True, index=True)
    amount: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    currency: str = Field(default="usd")
    status: str  # paid, open, void, uncollectible
    invoice_pdf: Optional[str] = None
    invoice_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, server_default=func.now())
    )


# Pydantic models for API requests/responses
class SubscriptionResponse(SQLModel):
    """Subscription response model."""

    id: str
    user_id: str
    stripe_subscription_id: str
    stripe_customer_id: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None


class QuotaResponse(SQLModel):
    """Quota response model."""

    id: str
    subscription_id: str
    user_id: str
    max_tokens: int
    max_api_calls: int
    max_scraping_tasks: int


class UsageResponse(SQLModel):
    """Usage response model."""

    id: str
    user_id: str
    subscription_id: Optional[str] = None
    usage_type: UsageType
    quantity: int
    period_start: datetime
    period_end: datetime


class UsageSummary(SQLModel):
    """Usage summary for a period."""

    user_id: str
    period_start: datetime
    period_end: datetime
    tokens_used: int
    api_calls_used: int
    scraping_tasks_used: int
    tokens_limit: int
    api_calls_limit: int
    scraping_tasks_limit: int


class InvoiceResponse(SQLModel):
    """Invoice response model."""

    id: str
    user_id: str
    subscription_id: Optional[str] = None
    stripe_invoice_id: str
    amount: Decimal
    currency: str
    status: str
    invoice_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class CreateCheckoutSessionRequest(SQLModel):
    """Request to create Stripe checkout session."""

    price_id: str
    success_url: str
    cancel_url: str


class CreateCheckoutSessionResponse(SQLModel):
    """Response with checkout session URL."""

    session_id: str
    url: str


class CreatePortalSessionResponse(SQLModel):
    """Response with customer portal session URL."""

    url: str
