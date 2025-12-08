"""Billing router for Stripe subscriptions and usage."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlmodel import Session, select
from typing import List, Optional
from .database import get_session
from .dependencies import get_current_user, get_current_active_user
from .models import User
from .auth import Role
from .billing_service import BillingService
from .billing_models import (
    SubscriptionResponse,
    QuotaResponse,
    UsageResponse,
    UsageSummary,
    InvoiceResponse,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    CreatePortalSessionResponse,
    UsageType,
)
from .config import get_settings

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()


@router.post("/checkout", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Create a Stripe checkout session for subscription."""
    try:
        frontend_url = settings.frontend_url
        result = BillingService.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            price_id=request.price_id,
            success_url=f"{frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/billing/cancel",
        )
        return CreateCheckoutSessionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/portal", response_model=CreatePortalSessionResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Create a Stripe customer portal session."""
    try:
        # Get user's subscription to find customer_id
        from .billing_models import Subscription
        
        subscription = session.exec(
            select(Subscription)
            .where(Subscription.user_id == current_user.id)
            .order_by(Subscription.created_at.desc())
        ).first()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found",
            )

        frontend_url = settings.frontend_url
        result = BillingService.create_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=f"{frontend_url}/billing",
        )
        return CreatePortalSessionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get current user's subscription."""
    from .billing_models import Subscription

    subscription = session.exec(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    ).first()

    if not subscription:
        return None

    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        stripe_subscription_id=subscription.stripe_subscription_id,
        stripe_customer_id=subscription.stripe_customer_id,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
    )


@router.get("/quota", response_model=Optional[QuotaResponse])
async def get_quota(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get current user's quota."""
    from .billing_models import Subscription, Quota

    subscription = session.exec(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    ).first()

    if not subscription:
        return None

    quota = session.exec(
        select(Quota).where(Quota.subscription_id == subscription.id)
    ).first()

    if not quota:
        return None

    return QuotaResponse(
        id=quota.id,
        subscription_id=quota.subscription_id,
        user_id=quota.user_id,
        max_tokens=quota.max_tokens,
        max_api_calls=quota.max_api_calls,
        max_scraping_tasks=quota.max_scraping_tasks,
    )


@router.get("/usage", response_model=UsageSummary)
async def get_usage(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get current user's usage summary."""
    return BillingService.get_usage_summary(session, current_user.id)


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    limit: int = 10,
):
    """Get current user's invoices."""
    from .billing_models import Invoice

    invoices = session.exec(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .limit(limit)
    ).all()

    return [
        InvoiceResponse(
            id=inv.id,
            user_id=inv.user_id,
            subscription_id=inv.subscription_id,
            stripe_invoice_id=inv.stripe_invoice_id,
            amount=inv.amount,
            currency=inv.currency,
            status=inv.status,
            invoice_url=inv.invoice_url,
            period_start=inv.period_start,
            period_end=inv.period_end,
            paid_at=inv.paid_at,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


# Admin endpoints
@router.get("/admin/users", response_model=List[dict])
async def get_all_users(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    limit: int = 100,
):
    """Get all users with subscription info (admin only)."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    from .billing_models import Subscription, Quota, Usage
    from datetime import datetime

    users = session.exec(select(User).limit(limit)).all()
    result = []

    for user in users:
        subscription = session.exec(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .order_by(Subscription.created_at.desc())
        ).first()

        quota = None
        if subscription:
            quota = session.exec(
                select(Quota).where(Quota.subscription_id == subscription.id)
            ).first()

        # Get current month usage
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        usage_summary = BillingService.get_usage_summary(session, user.id, period_start)

        result.append(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "subscription_status": subscription.status.value if subscription else None,
                "quota": {
                    "max_tokens": quota.max_tokens if quota else 0,
                    "max_api_calls": quota.max_api_calls if quota else 0,
                    "max_scraping_tasks": quota.max_scraping_tasks if quota else 0,
                },
                "usage": {
                    "tokens_used": usage_summary.tokens_used,
                    "api_calls_used": usage_summary.api_calls_used,
                    "scraping_tasks_used": usage_summary.scraping_tasks_used,
                },
            }
        )

    return result


@router.get("/admin/invoices", response_model=List[InvoiceResponse])
async def get_all_invoices(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    limit: int = 100,
):
    """Get all invoices (admin only)."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    from .billing_models import Invoice

    invoices = session.exec(
        select(Invoice).order_by(Invoice.created_at.desc()).limit(limit)
    ).all()

    return [
        InvoiceResponse(
            id=inv.id,
            user_id=inv.user_id,
            subscription_id=inv.subscription_id,
            stripe_invoice_id=inv.stripe_invoice_id,
            amount=inv.amount,
            currency=inv.currency,
            status=inv.status,
            invoice_url=inv.invoice_url,
            period_start=inv.period_start,
            period_end=inv.period_end,
            paid_at=inv.paid_at,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


# Webhook endpoint
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    session: Session = Depends(get_session),
):
    """Handle Stripe webhooks."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    # Handle the event
    event_type = event["type"]
    data = event["data"]["object"]

    try:
        if event_type == "customer.subscription.created":
            subscription = stripe.Subscription.retrieve(data["id"])
            BillingService.sync_subscription_from_stripe(session, subscription)

        elif event_type == "customer.subscription.updated":
            subscription = stripe.Subscription.retrieve(data["id"])
            BillingService.sync_subscription_from_stripe(session, subscription)

        elif event_type == "customer.subscription.deleted":
            subscription = stripe.Subscription.retrieve(data["id"])
            BillingService.sync_subscription_from_stripe(session, subscription)

        elif event_type == "invoice.paid":
            invoice = stripe.Invoice.retrieve(data["id"])
            BillingService.sync_invoice_from_stripe(session, invoice)

        elif event_type == "invoice.payment_failed":
            invoice = stripe.Invoice.retrieve(data["id"])
            BillingService.sync_invoice_from_stripe(session, invoice)

        return {"status": "success"}
    except Exception as e:
        # Log error but don't fail webhook
        print(f"Error processing webhook {event_type}: {str(e)}")
        return {"status": "error", "message": str(e)}
