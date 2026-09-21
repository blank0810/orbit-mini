"""Generate a demo subscriber in any status, for rehearsals and for the video.

    python -m app.generate_demo                      # active, on Pro
    python -m app.generate_demo --status past_due
    python -m app.generate_demo --status incomplete --plan starter
    python -m app.generate_demo --email you@example.com

Distinct from `seed_demo`, which maintains the ONE advertised account whose credentials
are printed on the login page. This makes throwaway accounts, each with its own address,
so several can exist at once.

Why it accepts a status: the dashboard renders four visually distinct states, and three of
them are awkward to reach by hand. Reproducing `past_due` honestly would mean a failing
card and a retry cycle; reproducing `canceled` means waiting out a period. Generating them
is how those states get seen, and every generated row carries obviously fake Stripe ids so
none of it can be mistaken for evidence that the webhook works.
"""

from __future__ import annotations

import argparse
import secrets
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models.subscriber_model import SUBSCRIBER_STATUSES, Subscriber
from app.repositories import subscriber_repository
from app.services.auth_service import hash_password

DEFAULT_PASSWORD = "orbit-demo-2026"
PLAN_NAMES = {"starter": "ScaleSage Starter", "pro": "ScaleSage Pro"}


def generate(
    *, status: str, plan: str, email: str | None = None, password: str = DEFAULT_PASSWORD
) -> tuple[str, str]:
    """Create one demo subscriber. Returns (email, password)."""
    if status not in SUBSCRIBER_STATUSES:
        raise SystemExit(f"status must be one of {', '.join(SUBSCRIBER_STATUSES)}")
    if plan not in PLAN_NAMES:
        raise SystemExit(f"plan must be one of {', '.join(PLAN_NAMES)}")

    address = email or f"demo-{secrets.token_hex(3)}@orbit.ehnand.com"
    session = SessionLocal()
    try:
        if subscriber_repository.get_by_email(session, address) is not None:
            raise SystemExit(f"{address} already exists")

        subscriber = Subscriber(
            email=address,
            first_name="Demo",
            last_name=status.replace("_", " ").title(),
            password_hash=hash_password(password),
            # An unpaid account has not chosen a plan yet, which is what the dashboard's
            # empty state is for.
            plan_name=PLAN_NAMES[plan] if status != "incomplete" else "none",
            status=status,
        )
        if status != "incomplete":
            subscriber.stripe_customer_id = "cus_demo_generated"
            subscriber.stripe_subscription_id = "sub_demo_generated"
            # canceled shows access-until in the past; everything else renews ahead.
            days = -3 if status == "canceled" else 30
            subscriber.current_period_end = datetime.now(UTC) + timedelta(days=days)
        subscriber_repository.create(session, subscriber)
        session.commit()
    finally:
        session.close()
    return address, password


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a demo subscriber.")
    parser.add_argument("--status", default="active", choices=list(SUBSCRIBER_STATUSES))
    parser.add_argument("--plan", default="pro", choices=list(PLAN_NAMES))
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()
    generated_email, generated_password = generate(
        status=args.status, plan=args.plan, email=args.email, password=args.password
    )
    print(f"  email:    {generated_email}")
    print(f"  password: {generated_password}")
    print(f"  status:   {args.status}")
