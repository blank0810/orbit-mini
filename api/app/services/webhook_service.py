"""Webhook delivery is at-least-once, so every path here must be safe to run twice.

Stripe is the source of truth for status; we never invent one.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository as repo
from app.services import stripe_client

# Stripe has eight statuses, the dashboard shows four visually distinct states.
# Every value produced here is still one Stripe itself uses: this normalises Stripe's
# vocabulary, it does not invent a local one. An unmapped status leaves the row unchanged
# rather than guessing.
STRIPE_STATUS_MAP: dict[str, str] = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "canceled": "canceled",
    "incomplete_expired": "canceled",
    "incomplete": "incomplete",
    "paused": "incomplete",
}


def _period_end(subscription: dict[str, Any]) -> datetime | None:
    timestamp = subscription.get("current_period_end")
    if timestamp is None:
        # Newer Stripe API versions moved the period end onto the subscription item.
        items = subscription.get("items", {}).get("data", [])
        if items:
            timestamp = items[0].get("current_period_end")
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _apply_subscription_period(subscriber: Subscriber, subscription_id: str) -> None:
    """Fill in status and billing period by reading the subscription from Stripe."""
    try:
        subscription = stripe_client.retrieve_subscription(subscription_id)
    except Exception:  # noqa: BLE001 - deliberately broad
        # A failed lookup must never fail the webhook. Anything other than 2xx makes Stripe
        # retry the whole delivery, and the period still arrives with the subscription
        # events. Missing a renewal date for a few seconds beats a retry storm.
        return
    period_end = _period_end(subscription)
    if period_end is not None:
        subscriber.current_period_end = period_end
    mapped = STRIPE_STATUS_MAP.get(str(subscription.get("status", "")))
    if mapped is not None:
        subscriber.status = mapped
    subscriber.cancel_at_period_end = bool(subscription.get("cancel_at_period_end", False))


def apply_event(session: Session, event: dict[str, Any]) -> str:
    event_id = event["id"]
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        reference_id = data.get("client_reference_id")
        try:
            subscriber_id = UUID(reference_id) if isinstance(reference_id, str) else None
        except ValueError:
            subscriber_id = None
        if subscriber_id is not None:
            subscriber = repo.get_by_id(session, subscriber_id)
        else:
            customer_id = data.get("customer")
            # Missing IDs must not match subscribers whose Stripe customer ID is also NULL.
            subscriber = (
                repo.get_by_stripe_customer_id(session, customer_id) if customer_id else None
            )
    elif event_type in (
        # created matters as much as updated: it is the event Stripe fires for a brand new
        # subscription, and it is the one that carries the first billing period.
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        subscriber = repo.get_by_stripe_subscription_id(session, data["id"])
        if subscriber is None:
            customer_id = data.get("customer")
            subscriber = (
                repo.get_by_stripe_customer_id(session, customer_id) if customer_id else None
            )
    else:
        return "unknown"

    # Stripe sends events for the whole account, including customers we do not have.
    if subscriber is None:
        return "ignored"

    # Stripe retries until it gets a 2xx, so the same event id arrives more than once.
    # Processing it twice must leave the row byte-identical.
    if subscriber.last_stripe_event_id == event_id:
        return "duplicate"

    if event_type == "checkout.session.completed":
        subscriber.status = "active"
        subscription_id = data.get("subscription")
        if not subscriber.stripe_subscription_id:
            subscriber.stripe_subscription_id = subscription_id
        if not subscriber.stripe_customer_id:
            subscriber.stripe_customer_id = data.get("customer")
        # A Checkout session has no billing period on it. Without this lookup the dashboard
        # shows Active with a blank renewal date until some later subscription event lands.
        if subscription_id:
            _apply_subscription_period(subscriber, subscription_id)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        # Stripe owns this flag. A cancellation scheduled or called off anywhere - our UI,
        # the Stripe dashboard, a dunning rule - arrives here.
        subscriber.cancel_at_period_end = bool(data.get("cancel_at_period_end", False))
        status = STRIPE_STATUS_MAP.get(data["status"])
        if status is not None:
            subscriber.status = status
        subscriber.current_period_end = _period_end(data)
        if not subscriber.stripe_subscription_id:
            subscriber.stripe_subscription_id = data["id"]
    elif event_type == "customer.subscription.deleted":
        subscriber.status = "canceled"
        # The scheduled cancellation has now happened; the flag has nothing left to say.
        subscriber.cancel_at_period_end = False
        period_end = _period_end(data)
        if period_end is not None:
            subscriber.current_period_end = period_end

    subscriber.last_stripe_event_id = event_id
    # The controller commits the mutation and replay guard together in one transaction.
    repo.save(session, subscriber)
    return "applied"
