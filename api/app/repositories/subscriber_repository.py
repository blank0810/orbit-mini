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


def count_disposable(session: Session) -> int:
    """How many generated demo rows exist."""
    return len(list(session.scalars(select(Subscriber).where(Subscriber.is_disposable.is_(True)))))


def oldest_disposable(session: Session) -> Subscriber | None:
    """The generated demo row that has existed longest.

    Every query here filters on is_disposable. Eviction must never be able to reach the
    advertised demo account or a real customer, and the filter is what guarantees that
    rather than the caller remembering to check.
    """
    return session.scalars(
        select(Subscriber)
        .where(Subscriber.is_disposable.is_(True))
        .order_by(Subscriber.created_at.asc())
        .limit(1)
    ).one_or_none()


def delete(session: Session, subscriber: Subscriber) -> None:
    """Remove a row. Flushes but does not commit, like the rest of this module."""
    session.delete(subscriber)
    session.flush()
