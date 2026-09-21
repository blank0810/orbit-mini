from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscriber_model import Subscriber


def get_by_email(session: Session, email: str) -> Subscriber | None:
    return session.scalars(select(Subscriber).where(Subscriber.email == email)).one_or_none()


def get_by_id(session: Session, subscriber_id: UUID) -> Subscriber | None:
    return session.scalars(select(Subscriber).where(Subscriber.id == subscriber_id)).one_or_none()


def get_by_stripe_customer_id(session: Session, customer_id: str) -> Subscriber | None:
    return session.scalars(
        select(Subscriber).where(Subscriber.stripe_customer_id == customer_id)
    ).one_or_none()


def get_by_stripe_subscription_id(session: Session, subscription_id: str) -> Subscriber | None:
    return session.scalars(
        select(Subscriber).where(Subscriber.stripe_subscription_id == subscription_id)
    ).one_or_none()


# Create and save flush but never commit: callers own transactions so webhook changes are atomic.
def create(session: Session, subscriber: Subscriber) -> Subscriber:
    session.add(subscriber)
    session.flush()
    return subscriber


def save(session: Session, subscriber: Subscriber) -> Subscriber:
    session.flush()
    return subscriber
