"""Seed the demo account the login page advertises.

Run explicitly, never on startup:

    docker compose -f infra/docker-compose.yml exec api python -m app.seed_demo

An ENVIRONMENT-conditional seed on boot would be a config knob, and every knob is a
decision someone has to make later while debugging. This is one command, run when wanted.

The row is deliberately, visibly seeded. Its Stripe subscription id is `sub_demo_seeded`,
which matches nothing in Stripe, so nobody can mistake this for evidence that the webhook
works. The webhook is demonstrated by a real payment, not by this.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.services.auth_service import hash_password

DEMO_EMAIL = "demo@orbit.ehnand.com"
DEMO_PASSWORD = "orbit-demo-2026"


def seed() -> str:
    """Create or refresh the demo subscriber. Safe to run repeatedly."""
    session = SessionLocal()
    try:
        period_end = datetime.now(UTC) + timedelta(days=30)
        subscriber = subscriber_repository.get_by_email(session, DEMO_EMAIL)
        created = subscriber is None

        if subscriber is None:
            subscriber = Subscriber(
                email=DEMO_EMAIL,
                first_name="Demo",
                last_name="Account",
                password_hash=hash_password(DEMO_PASSWORD),
                plan_name="ScaleSage Pro",
                status="active",
                # Never disposable: its credentials are printed on the login page, so the
                # cap must not be able to evict it and make them stale.
                is_disposable=False,
            )
            subscriber_repository.create(session, subscriber)
        else:
            # Refresh rather than skip, so a demo left in a strange state by an earlier
            # run comes back clean before a recording.
            subscriber.password_hash = hash_password(DEMO_PASSWORD)
            subscriber.plan_name = "ScaleSage Pro"
            subscriber.status = "active"

        subscriber.is_disposable = False
        subscriber.stripe_customer_id = "cus_demo_seeded"
        subscriber.stripe_subscription_id = "sub_demo_seeded"
        subscriber.current_period_end = period_end
        subscriber_repository.save(session, subscriber)
        session.commit()
        return "created" if created else "refreshed"
    finally:
        session.close()


if __name__ == "__main__":
    outcome = seed()
    print(f"demo account {outcome}: {DEMO_EMAIL}")
