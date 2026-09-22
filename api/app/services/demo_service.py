"""Generated, disposable demo accounts.

The public site offers a one-click demo account. That is an unauthenticated endpoint that
creates rows, so it is bounded on purpose: at most MAX_DISPOSABLE demo accounts exist at
any time, and asking for one more evicts the oldest instead of growing the table.

Eviction only ever touches rows flagged `is_disposable`. The advertised demo account whose
credentials are printed on the login page is deliberately NOT flagged, so it cannot be
evicted and the printed credentials cannot go stale. Real customers are never flagged
either, so the cap can never reach them.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.subscriber_model import SUBSCRIBER_STATUSES, Subscriber
from app.repositories import subscriber_repository
from app.services.auth_service import hash_password

MAX_DISPOSABLE = 5
DEMO_PASSWORD = "orbit-demo-2026"
PLAN_NAMES = {"starter": "ScaleSage Starter", "pro": "ScaleSage Pro"}

# Fake by design. A generated row must never be mistakable for evidence that a real payment
# was recorded, so these ids match nothing in Stripe and are excluded from Stripe cleanup.
DEMO_CUSTOMER_ID = "cus_demo_generated"
DEMO_SUBSCRIPTION_ID = "sub_demo_generated"


class UnknownDemoStatus(Exception):
    """Raised when a status outside the subscriber vocabulary is requested."""


def evict_to_make_room(session: Session, *, limit: int = MAX_DISPOSABLE) -> list[str]:
    """Delete oldest disposable demos until there is room for one more.

    A loop rather than a single delete, so the cap still converges if extra rows exist for
    any reason. Returns the evicted addresses for logging.
    """
    evicted: list[str] = []
    while subscriber_repository.count_disposable(session) >= limit:
        oldest = subscriber_repository.oldest_disposable(session)
        if oldest is None:
            # Count and fetch disagreeing would spin forever. Stop rather than loop.
            break
        evicted.append(oldest.email)
        subscriber_repository.delete(session, oldest)
    return evicted


def generate(
    session: Session, *, status: str = "active", plan: str = "pro"
) -> tuple[Subscriber, str, list[str]]:
    """Create one disposable demo account. Returns (subscriber, password, evicted emails).

    Does not commit; the caller owns the transaction so the eviction and the insert land
    together. A crash between them would otherwise leave the table one short.
    """
    if status not in SUBSCRIBER_STATUSES:
        raise UnknownDemoStatus(status)
    if plan not in PLAN_NAMES:
        raise UnknownDemoStatus(plan)

    evicted = evict_to_make_room(session)

    subscriber = Subscriber(
        email=f"demo-{secrets.token_hex(3)}@orbit.ehnand.com",
        first_name="Demo",
        last_name="User",
        password_hash=hash_password(DEMO_PASSWORD),
        plan_name=PLAN_NAMES[plan] if status != "incomplete" else "none",
        status=status,
        is_disposable=True,
    )
    if status != "incomplete":
        subscriber.stripe_customer_id = DEMO_CUSTOMER_ID
        subscriber.stripe_subscription_id = DEMO_SUBSCRIPTION_ID
        # canceled reads as access-until in the past; everything else renews ahead.
        subscriber.current_period_end = datetime.now(UTC) + timedelta(
            days=-3 if status == "canceled" else 30
        )
    subscriber_repository.create(session, subscriber)
    return subscriber, DEMO_PASSWORD, evicted
