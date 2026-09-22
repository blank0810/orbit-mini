from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.services import plan_catalogue, stripe_client


class AlreadySubscribed(Exception):
    pass


class NotSubscribed(Exception):
    """Raised when a plan change is attempted without a live subscription to change."""


class AlreadyOnPlan(Exception):
    """Raised when the requested plan is the one already held."""


class NotCancellable(Exception):
    """Raised when there is no live subscription to cancel or resume."""


def start_checkout(session: Session, subscriber: Subscriber, plan_key: str) -> str:
    plan = plan_catalogue.get_plan(plan_key)
    # A second Checkout for an active subscriber would create a second Stripe
    # subscription and bill them twice.
    if subscriber.status == "active":
        raise AlreadySubscribed

    price_id = stripe_client.resolve_price_id(plan.product_id)
    settings = get_settings()
    # Stripe substitutes this literal placeholder; doubled braces preserve it in an f-string.
    success_url = f"{settings.web_base_url}/pending?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.web_base_url}/"
    checkout = stripe_client.create_checkout_session(
        subscriber_id=subscriber.id,
        email=subscriber.email,
        customer_id=subscriber.stripe_customer_id,
        price_id=price_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    if checkout.customer_id and not subscriber.stripe_customer_id:
        subscriber.stripe_customer_id = checkout.customer_id
    # The stored name and charged price come from the same server-owned plan mapping.
    subscriber.plan_name = plan.display_name
    subscriber_repository.save(session, subscriber)
    return checkout.url


def change_plan(session: Session, subscriber: Subscriber, plan_key: str) -> str:
    """Move an existing subscriber between plans, prorated. Returns the new plan name.

    Deliberately separate from start_checkout. Starting a checkout for someone who already
    pays would open a SECOND Stripe subscription and bill them twice; this repoints the one
    they have.
    """
    plan = plan_catalogue.get_plan(plan_key)

    if subscriber.status != "active" or not subscriber.stripe_subscription_id:
        raise NotSubscribed
    if subscriber.plan_name == plan.display_name:
        raise AlreadyOnPlan

    price_id = stripe_client.resolve_price_id(plan.product_id)
    stripe_client.change_subscription_price(subscriber.stripe_subscription_id, price_id)

    # Written from the server-side catalogue, not from the Stripe response, so the stored
    # name can never disagree with the price the customer was actually moved onto. The
    # customer.subscription.updated webhook will follow and refresh status and period.
    subscriber.plan_name = plan.display_name
    subscriber_repository.save(session, subscriber)
    return plan.display_name


def _live_subscription_id(subscriber: Subscriber) -> str:
    if subscriber.status not in ("active", "past_due") or not subscriber.stripe_subscription_id:
        raise NotCancellable
    return subscriber.stripe_subscription_id


def cancel(session: Session, subscriber: Subscriber) -> None:
    """Schedule cancellation at the end of the paid period."""
    stripe_client.set_cancel_at_period_end(_live_subscription_id(subscriber), cancel=True)
    # Status deliberately unchanged: Stripe keeps it active until the period lapses, and
    # this row mirrors Stripe rather than running ahead of it.
    subscriber.cancel_at_period_end = True
    subscriber_repository.save(session, subscriber)


def resume(session: Session, subscriber: Subscriber) -> None:
    """Call off a scheduled cancellation, while the period is still running."""
    stripe_client.set_cancel_at_period_end(_live_subscription_id(subscriber), cancel=False)
    subscriber.cancel_at_period_end = False
    subscriber_repository.save(session, subscriber)
