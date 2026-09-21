"""The only module that imports Stripe.

The test suite stubs exactly these boundary functions, which makes the required tests
writable without live Stripe calls or raw Stripe objects leaking into business logic.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import stripe

from app.core.config import get_settings


class StripeNotConfigured(Exception):
    pass


class InvalidWebhookSignature(Exception):
    pass


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str
    customer_id: str | None


def _require_key() -> str:
    key = get_settings().stripe_secret_key
    if not key:
        raise StripeNotConfigured("STRIPE_SECRET_KEY is not configured")
    return key


def create_checkout_session(
    *,
    subscriber_id: UUID,
    email: str,
    customer_id: str | None,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    settings = get_settings()
    api_key = _require_key()
    if not settings.stripe_price_id:
        raise StripeNotConfigured("STRIPE_PRICE_ID is not configured")
    customer_options = {"customer": customer_id} if customer_id else {"customer_email": email}
    checkout = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        # CRITICAL: this is the ONLY link from completed Checkout to our subscriber row.
        # Stripe echoes it on the webhook event; without it we cannot identify whose
        # subscription just activated.
        client_reference_id=str(subscriber_id),
        **customer_options,
        success_url=success_url,
        cancel_url=cancel_url,
        api_key=api_key,
    )
    if not checkout.url:
        raise ValueError("Stripe Checkout did not return a checkout URL")
    customer = checkout.customer
    return CheckoutSession(
        id=checkout.id,
        url=checkout.url,
        customer_id=customer if isinstance(customer, str) else customer.id if customer else None,
    )


def construct_event(payload: bytes, signature_header: str) -> dict[str, Any]:
    secret = get_settings().stripe_webhook_secret
    # An empty signing secret must never become an accepted webhook verification key.
    if not secret:
        raise StripeNotConfigured("STRIPE_WEBHOOK_SECRET is not configured")
    try:
        event = stripe.Webhook.construct_event(payload, signature_header, secret)
    except (stripe.SignatureVerificationError, ValueError):
        raise InvalidWebhookSignature("Invalid webhook signature or payload") from None
    return dict(event)
