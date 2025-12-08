"""Billing service for Stripe subscriptions and usage tracking."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from decimal import Decimal
import stripe
from sqlmodel import Session, select
from .config import get_settings
from .billing_models import (
    Subscription,
    Quota,
    Usage,
    Invoice,
    SubscriptionStatus,
    UsageType,
    UsageSummary,
)
from .models import User

settings = get_settings()

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class BillingService:
    """Service for managing billing, subscriptions, and usage."""

    @staticmethod
    def create_checkout_session(
        user_id: str,
        user_email: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict:
        """Create a Stripe checkout session."""
        try:
            # Get or create Stripe customer
            customer = BillingService.get_or_create_customer(user_id, user_email)

            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id},
            )

            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            raise Exception(f"Failed to create checkout session: {str(e)}")

    @staticmethod
    def get_or_create_customer(user_id: str, user_email: str) -> stripe.Customer:
        """Get or create a Stripe customer for a user."""
        # Check if user already has a customer ID in subscription
        # For now, create new customer - in production, store customer_id in User model
        try:
            customers = stripe.Customer.list(email=user_email, limit=1)
            if customers.data:
                return customers.data[0]

            customer = stripe.Customer.create(
                email=user_email,
                metadata={"user_id": user_id},
            )
            return customer
        except Exception as e:
            raise Exception(f"Failed to get or create customer: {str(e)}")

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> Dict:
        """Create a Stripe customer portal session."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return {"url": session.url}
        except Exception as e:
            raise Exception(f"Failed to create portal session: {str(e)}")

    @staticmethod
    def sync_subscription_from_stripe(
        session: Session, stripe_subscription: stripe.Subscription
    ) -> Subscription:
        """Sync subscription data from Stripe webhook."""
        # Find subscription by stripe_subscription_id
        existing = session.exec(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription.id
            )
        ).first()

        # Get customer metadata to find user_id
        customer = stripe.Customer.retrieve(stripe_subscription.customer)
        user_id = customer.metadata.get("user_id")

        if not user_id:
            # Try to find by email
            user = session.exec(select(User).where(User.email == customer.email)).first()
            if user:
                user_id = user.id
            else:
                raise Exception(f"Could not find user for customer {customer.id}")

        subscription_data = {
            "id": existing.id if existing else str(uuid.uuid4()),
            "user_id": user_id,
            "stripe_subscription_id": stripe_subscription.id,
            "stripe_customer_id": stripe_subscription.customer,
            "stripe_price_id": stripe_subscription.items.data[0].price.id
            if stripe_subscription.items.data
            else None,
            "status": SubscriptionStatus(stripe_subscription.status),
            "current_period_start": datetime.fromtimestamp(
                stripe_subscription.current_period_start
            ),
            "current_period_end": datetime.fromtimestamp(
                stripe_subscription.current_period_end
            ),
            "cancel_at_period_end": stripe_subscription.cancel_at_period_end,
            "canceled_at": datetime.fromtimestamp(stripe_subscription.canceled_at)
            if stripe_subscription.canceled_at
            else None,
            "trial_start": datetime.fromtimestamp(stripe_subscription.trial_start)
            if stripe_subscription.trial_start
            else None,
            "trial_end": datetime.fromtimestamp(stripe_subscription.trial_end)
            if stripe_subscription.trial_end
            else None,
        }

        if existing:
            for key, value in subscription_data.items():
                if key != "id":
                    setattr(existing, key, value)
            subscription = existing
        else:
            subscription = Subscription(**subscription_data)
            session.add(subscription)

        session.commit()
        session.refresh(subscription)

        # Sync quota based on price
        BillingService.sync_quota_from_subscription(session, subscription)

        return subscription

    @staticmethod
    def sync_quota_from_subscription(
        session: Session, subscription: Subscription
    ) -> Quota:
        """Sync quota limits based on subscription plan."""
        # Find existing quota
        existing = session.exec(
            select(Quota).where(Quota.subscription_id == subscription.id)
        ).first()

        # Define quota limits based on price_id (you can customize this)
        price_id = subscription.stripe_price_id
        quota_limits = BillingService.get_quota_limits_for_price(price_id)

        quota_data = {
            "id": existing.id if existing else str(uuid.uuid4()),
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "max_tokens": quota_limits["max_tokens"],
            "max_api_calls": quota_limits["max_api_calls"],
            "max_scraping_tasks": quota_limits["max_scraping_tasks"],
        }

        if existing:
            for key, value in quota_data.items():
                if key != "id":
                    setattr(existing, key, value)
            quota = existing
        else:
            quota = Quota(**quota_data)
            session.add(quota)

        session.commit()
        session.refresh(quota)
        return quota

    @staticmethod
    def get_quota_limits_for_price(price_id: Optional[str]) -> Dict[str, int]:
        """Get quota limits for a given Stripe price ID."""
        # Default limits (free tier)
        limits = {
            "max_tokens": 10000,
            "max_api_calls": 100,
            "max_scraping_tasks": 10,
        }

        if not price_id:
            return limits

        settings = get_settings()

        # Map price IDs to limits
        if price_id == settings.stripe_price_basic:
            limits = {
                "max_tokens": 100000,
                "max_api_calls": 1000,
                "max_scraping_tasks": 100,
            }
        elif price_id == settings.stripe_price_pro:
            limits = {
                "max_tokens": 1000000,
                "max_api_calls": 10000,
                "max_scraping_tasks": 1000,
            }
        elif price_id == settings.stripe_price_enterprise:
            limits = {
                "max_tokens": 0,  # unlimited
                "max_api_calls": 0,  # unlimited
                "max_scraping_tasks": 0,  # unlimited
            }

        return limits

    @staticmethod
    def sync_invoice_from_stripe(
        session: Session, stripe_invoice: stripe.Invoice
    ) -> Invoice:
        """Sync invoice data from Stripe webhook."""
        existing = session.exec(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice.id)
        ).first()

        # Get customer to find user_id
        customer = stripe.Customer.retrieve(stripe_invoice.customer)
        user_id = customer.metadata.get("user_id")

        if not user_id:
            user = session.exec(select(User).where(User.email == customer.email)).first()
            if user:
                user_id = user.id
            else:
                raise Exception(f"Could not find user for customer {customer.id}")

        # Get subscription_id if exists
        subscription_id = None
        if stripe_invoice.subscription:
            sub = session.exec(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_invoice.subscription
                )
            ).first()
            if sub:
                subscription_id = sub.id

        invoice_data = {
            "id": existing.id if existing else str(uuid.uuid4()),
            "user_id": user_id,
            "subscription_id": subscription_id,
            "stripe_invoice_id": stripe_invoice.id,
            "amount": Decimal(stripe_invoice.amount_paid) / 100,
            "currency": stripe_invoice.currency,
            "status": stripe_invoice.status,
            "invoice_pdf": stripe_invoice.invoice_pdf,
            "invoice_url": stripe_invoice.hosted_invoice_url,
            "period_start": datetime.fromtimestamp(stripe_invoice.period_start)
            if stripe_invoice.period_start
            else None,
            "period_end": datetime.fromtimestamp(stripe_invoice.period_end)
            if stripe_invoice.period_end
            else None,
            "paid_at": datetime.fromtimestamp(stripe_invoice.status_transitions.paid_at)
            if stripe_invoice.status_transitions.paid_at
            else None,
        }

        if existing:
            for key, value in invoice_data.items():
                if key != "id":
                    setattr(existing, key, value)
            invoice = existing
        else:
            invoice = Invoice(**invoice_data)
            session.add(invoice)

        session.commit()
        session.refresh(invoice)
        return invoice

    @staticmethod
    def record_usage(
        session: Session,
        user_id: str,
        usage_type: UsageType,
        quantity: int,
        metadata: Optional[Dict] = None,
    ) -> Usage:
        """Record usage for a user."""
        # Get current subscription
        subscription = session.exec(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.created_at.desc())
        ).first()

        # Get current period
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)

        # Check if usage record exists for this period
        existing = session.exec(
            select(Usage)
            .where(Usage.user_id == user_id)
            .where(Usage.usage_type == usage_type)
            .where(Usage.period_start == period_start)
            .where(Usage.period_end == period_end)
        ).first()

        if existing:
            existing.quantity += quantity
            if metadata:
                existing.metadata = metadata
            usage = existing
        else:
            usage = Usage(
                id=str(uuid.uuid4()),
                user_id=user_id,
                subscription_id=subscription.id if subscription else None,
                usage_type=usage_type,
                quantity=quantity,
                metadata=metadata,
                period_start=period_start,
                period_end=period_end,
            )
            session.add(usage)

        session.commit()
        session.refresh(usage)
        return usage

    @staticmethod
    def check_quota(
        session: Session, user_id: str, usage_type: UsageType, requested_quantity: int = 1
    ) -> tuple:
        """Check if user has quota available."""
        # Get active subscription
        subscription = session.exec(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.created_at.desc())
        ).first()

        if not subscription:
            return False, "No active subscription"

        # Get quota
        quota = session.exec(
            select(Quota).where(Quota.subscription_id == subscription.id)
        ).first()

        if not quota:
            return False, "No quota configured"

        # Get current usage for this period
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)

        usage = session.exec(
            select(Usage)
            .where(Usage.user_id == user_id)
            .where(Usage.usage_type == usage_type)
            .where(Usage.period_start == period_start)
            .where(Usage.period_end == period_end)
        ).first()

        current_usage = usage.quantity if usage else 0

        # Check limits
        if usage_type == UsageType.TOKENS:
            limit = quota.max_tokens
            if limit > 0 and (current_usage + requested_quantity) > limit:
                return False, f"Token quota exceeded ({current_usage}/{limit})"
        elif usage_type == UsageType.API_CALLS:
            limit = quota.max_api_calls
            if limit > 0 and (current_usage + requested_quantity) > limit:
                return False, f"API call quota exceeded ({current_usage}/{limit})"
        elif usage_type == UsageType.SCRAPING_TASKS:
            limit = quota.max_scraping_tasks
            if limit > 0 and (current_usage + requested_quantity) > limit:
                return False, f"Scraping task quota exceeded ({current_usage}/{limit})"

        return True, None

    @staticmethod
    def get_usage_summary(
        session: Session, user_id: str, period_start: Optional[datetime] = None
    ) -> UsageSummary:
        """Get usage summary for a user."""
        now = datetime.utcnow()
        if not period_start:
            period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)

        # Get subscription and quota
        subscription = session.exec(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.created_at.desc())
        ).first()

        quota = None
        if subscription:
            quota = session.exec(
                select(Quota).where(Quota.subscription_id == subscription.id)
            ).first()

        # Get usage for period
        tokens_usage = session.exec(
            select(Usage)
            .where(Usage.user_id == user_id)
            .where(Usage.usage_type == UsageType.TOKENS)
            .where(Usage.period_start == period_start)
            .where(Usage.period_end == period_end)
        ).first()

        api_calls_usage = session.exec(
            select(Usage)
            .where(Usage.user_id == user_id)
            .where(Usage.usage_type == UsageType.API_CALLS)
            .where(Usage.period_start == period_start)
            .where(Usage.period_end == period_end)
        ).first()

        scraping_tasks_usage = session.exec(
            select(Usage)
            .where(Usage.user_id == user_id)
            .where(Usage.usage_type == UsageType.SCRAPING_TASKS)
            .where(Usage.period_start == period_start)
            .where(Usage.period_end == period_end)
        ).first()

        return UsageSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            tokens_used=tokens_usage.quantity if tokens_usage else 0,
            api_calls_used=api_calls_usage.quantity if api_calls_usage else 0,
            scraping_tasks_used=scraping_tasks_usage.quantity if scraping_tasks_usage else 0,
            tokens_limit=quota.max_tokens if quota else 0,
            api_calls_limit=quota.max_api_calls if quota else 0,
            scraping_tasks_limit=quota.max_scraping_tasks if quota else 0,
        )
