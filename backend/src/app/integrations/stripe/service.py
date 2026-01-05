"""
Stripe integration service for billing operations.

Handles:
- Customer creation and management
- Subscription lifecycle
- Bid wallet deposits
- Webhook processing
"""
import asyncio
import stripe
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from src.app.config import settings
from src.app.models.professional import SubscriptionTier


class StripeService:
    """
    Service for Stripe payment operations.

    Manages subscriptions, one-time payments for bid credits,
    and customer portal sessions.
    """

    @property
    def tier_price_ids(self) -> Dict[SubscriptionTier, Optional[str]]:
        """Get tier to Stripe price ID mapping from config."""
        return {
            SubscriptionTier.BASIC: settings.stripe_price_id_basic,
            SubscriptionTier.PROFESSIONAL: settings.stripe_price_id_professional,
            SubscriptionTier.PREMIUM: settings.stripe_price_id_premium,
        }

    # Tier pricing for display
    TIER_PRICING = {
        SubscriptionTier.FREE: Decimal("0.00"),
        SubscriptionTier.BASIC: Decimal("49.00"),
        SubscriptionTier.PROFESSIONAL: Decimal("99.00"),
        SubscriptionTier.PREMIUM: Decimal("199.00"),
    }

    # Tier features
    TIER_FEATURES = {
        SubscriptionTier.FREE: [
            "Basic grid listing",
            "5 calls per month",
            "Standard support",
        ],
        SubscriptionTier.BASIC: [
            "Enhanced grid visibility",
            "25 calls per month",
            "Priority support",
            "Basic analytics",
        ],
        SubscriptionTier.PROFESSIONAL: [
            "Premium grid placement",
            "Unlimited calls",
            "Priority support",
            "Advanced analytics",
            "Featured badge",
        ],
        SubscriptionTier.PREMIUM: [
            "Top grid placement",
            "Unlimited calls",
            "24/7 dedicated support",
            "Full analytics suite",
            "Featured badge",
            "Custom profile branding",
            "Lead insights",
        ],
    }

    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret

    async def create_customer(
        self,
        user_id: UUID,
        email: str,
        name: str,
        metadata: dict = None,
    ) -> str:
        """
        Create a Stripe customer for a user.

        Returns the Stripe customer ID.
        """
        customer = await asyncio.to_thread(
            stripe.Customer.create,
            email=email,
            name=name,
            metadata={
                "user_id": str(user_id),
                **(metadata or {}),
            },
        )
        return customer.id

    async def get_or_create_customer(
        self,
        user_id: UUID,
        email: str,
        name: str,
        existing_customer_id: str = None,
    ) -> str:
        """Get existing customer or create new one."""
        if existing_customer_id:
            try:
                customer = await asyncio.to_thread(
                    stripe.Customer.retrieve, existing_customer_id
                )
                if not customer.deleted:
                    return customer.id
            except stripe.error.InvalidRequestError:
                pass

        return await self.create_customer(user_id, email, name)

    async def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        trial_days: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a subscription for a customer.

        Returns subscription details including client_secret for payment.
        """
        if tier == SubscriptionTier.FREE:
            raise ValueError("Cannot create subscription for free tier")

        price_id = self.tier_price_ids.get(tier)
        if not price_id:
            raise ValueError(f"No price configured for tier: {tier}. Set STRIPE_PRICE_ID_{tier.name} in environment.")

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "payment_settings": {
                "save_default_payment_method": "on_subscription",
            },
            "expand": ["latest_invoice.payment_intent"],
        }

        if trial_days > 0:
            subscription_params["trial_period_days"] = trial_days

        subscription = await asyncio.to_thread(
            stripe.Subscription.create, **subscription_params
        )

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "client_secret": (
                subscription.latest_invoice.payment_intent.client_secret
                if subscription.latest_invoice and subscription.latest_invoice.payment_intent
                else None
            ),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
        }

    async def update_subscription(
        self,
        subscription_id: str,
        new_tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """
        Update (upgrade/downgrade) a subscription.
        """
        if new_tier == SubscriptionTier.FREE:
            # Cancel subscription for downgrade to free
            return await self.cancel_subscription(subscription_id)

        price_id = self.tier_price_ids.get(new_tier)
        if not price_id:
            raise ValueError(f"No price configured for tier: {new_tier}. Set STRIPE_PRICE_ID_{new_tier.name} in environment.")

        subscription = await asyncio.to_thread(
            stripe.Subscription.retrieve, subscription_id
        )

        updated = await asyncio.to_thread(
            stripe.Subscription.modify,
            subscription_id,
            items=[
                {
                    "id": subscription["items"]["data"][0].id,
                    "price": price_id,
                }
            ],
            proration_behavior="create_prorations",
        )

        return {
            "subscription_id": updated.id,
            "status": updated.status,
            "current_period_end": datetime.fromtimestamp(updated.current_period_end),
        }

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        By default, cancels at the end of the billing period.
        """
        if at_period_end:
            subscription = await asyncio.to_thread(
                stripe.Subscription.modify,
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            subscription = await asyncio.to_thread(
                stripe.Subscription.delete, subscription_id
            )

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
        }

    async def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Reactivate a subscription that was set to cancel at period end."""
        subscription = await asyncio.to_thread(
            stripe.Subscription.modify,
            subscription_id,
            cancel_at_period_end=False,
        )

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
        }

    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details."""
        try:
            subscription = await asyncio.to_thread(
                stripe.Subscription.retrieve, subscription_id
            )
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.InvalidRequestError:
            return None

    async def create_bid_deposit_session(
        self,
        customer_id: str,
        amount_dollars: Decimal,
        professional_id: UUID,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Create a Checkout Session for depositing bid credits.

        Returns the checkout session URL.
        """
        # Amount in cents
        amount_cents = int(amount_dollars * 100)

        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": "Bid Credits",
                            "description": f"${amount_dollars} in bid credits for grid placement",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "type": "bid_deposit",
                "professional_id": str(professional_id),
                "amount": str(amount_dollars),
            },
        )

        return session.url

    async def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """
        Create a billing portal session for customer self-service.

        Allows customers to manage payment methods, view invoices, etc.
        """
        session = await asyncio.to_thread(
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str,
    ) -> stripe.Event:
        """Construct and verify a webhook event."""
        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            self.webhook_secret,
        )

    def get_tier_pricing(self) -> List[Dict[str, Any]]:
        """Get all tier pricing information."""
        return [
            {
                "tier": tier.value,
                "name": tier.name.replace("_", " ").title(),
                "price": float(price),
                "features": self.TIER_FEATURES.get(tier, []),
            }
            for tier, price in self.TIER_PRICING.items()
        ]


# Singleton instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get the Stripe service singleton."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
