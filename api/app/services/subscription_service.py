from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.services import plan_catalogue, stripe_client


class AlreadySubscribed(Exception):
    pass


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
