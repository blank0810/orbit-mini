"""The only module that imports Stripe.

The test suite stubs exactly these boundary functions, which makes the required tests
writable without live Stripe calls or raw Stripe objects leaking into business logic.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
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


# Resolution is cached per process, so changing a default price in Stripe needs a restart.
# This deliberately keeps a network call out of every checkout.
@lru_cache
def resolve_price_id(product_id: str) -> str:
    if not product_id:
        settings = get_settings()
        unset = [
            name
            for name, value in (
                ("STRIPE_PRODUCT_ID_STARTER", settings.stripe_product_id_starter),
                ("STRIPE_PRODUCT_ID_PRO", settings.stripe_product_id_pro),
            )
            if not value
        ]
        raise StripeNotConfigured(
            f"Stripe product id is unset: {', '.join(unset) or 'no product id supplied'}"
        )
    try:
        product = stripe.Product.retrieve(
            product_id, expand=["default_price"], api_key=_require_key()
        )
        price = getattr(product, "default_price", None)
        if not price:
            raise StripeNotConfigured(
                "The product has no default price set in Stripe; one must be added"
            )
        if isinstance(price, str):
            price = stripe.Price.retrieve(price, api_key=_require_key())
        # These mistakes stay silent until checkout fails in front of someone. Validating
        # at resolution lets startup callers fail early rather than during a demo checkout.
        if price.recurring is None:
            raise StripeNotConfigured(
                "The price is one-time, but subscription mode needs a recurring price"
            )
        if price.currency != "gbp":
            raise StripeNotConfigured(
                f"The price currency is {price.currency}; subscription prices must use gbp"
            )
        return price.id
    except stripe.InvalidRequestError:
        # Do not include Stripe's exception text: configuration errors must never expose keys.
        raise StripeNotConfigured(
            f"Could not resolve the default price for Stripe product {product_id}"
        ) from None


def create_checkout_session(
    *,
    subscriber_id: UUID,
    email: str,
    customer_id: str | None,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    api_key = _require_key()
    customer_options = {"customer": customer_id} if customer_id else {"customer_email": email}
    checkout = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
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
        stripe.Webhook.construct_event(payload, signature_header, secret)
    except (stripe.SignatureVerificationError, ValueError):
        raise InvalidWebhookSignature("Invalid webhook signature or payload") from None
    # construct_event is called for its verification side effect only. Its return value is a
    # stripe.Event, which is not a mapping in stripe-python 15.x, and to_dict() leaves nested
    # objects as StripeObject. The handlers walk nested structures, so parse the bytes we
    # already verified and hand back a plain recursive dict instead. This also keeps the rest
    # of the codebase free of any Stripe type.
    return json.loads(payload)


def cancel_subscription(subscription_id: str) -> str:
    """Cancel a subscription immediately. Returns its resulting status.

    Used only by the demo reset. Cancelling is safe to retry: a subscription already
    cancelled reports `canceled` rather than erroring, and one Stripe has never heard of
    raises InvalidRequestError, which the caller treats as already gone.
    """
    subscription = stripe.Subscription.cancel(subscription_id, api_key=_require_key())
    return str(subscription.status)


def delete_customer(customer_id: str) -> bool:
    """Delete a customer. Returns False when Stripe has no such customer.

    Test-mode customers accumulate with every rehearsal, and a dashboard full of them
    makes the real one hard to find during a recording.
    """
    try:
        result = stripe.Customer.delete(customer_id, api_key=_require_key())
    except stripe.InvalidRequestError:
        return False
    return bool(getattr(result, "deleted", False))
