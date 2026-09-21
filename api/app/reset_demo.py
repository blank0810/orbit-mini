"""Reset the demo deployment to a clean, recordable state.

DESTRUCTIVE. It cancels every real Stripe subscription this deployment created, deletes
the Stripe customers behind them, removes every subscriber row, and re-seeds the demo
account.

    docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml \\
        exec api python -m app.reset_demo --yes

`--yes` is a safety interlock, not a preference. Without it the script prints what it
would do and exits, because the difference between this and a production wipe is only
which database it is pointed at.

Stripe cleanup runs BEFORE the rows are deleted: the subscription ids live on those rows,
so deleting first would orphan live subscriptions that keep billing in test mode and keep
sending webhooks at a database that no longer knows who they belong to.
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.subscriber_model import Subscriber
from app.seed_demo import DEMO_EMAIL, seed
from app.services import stripe_client

# The seeded row carries deliberately fake Stripe ids so nobody mistakes it for webhook
# evidence. They must never be sent to Stripe.
SEEDED_IDS = {"sub_demo_seeded", "cus_demo_seeded"}


def _plan(session) -> tuple[list[Subscriber], list[str], list[str]]:
    rows = list(session.scalars(select(Subscriber)))
    subs = [
        r.stripe_subscription_id
        for r in rows
        if r.stripe_subscription_id and r.stripe_subscription_id not in SEEDED_IDS
    ]
    customers = [
        r.stripe_customer_id
        for r in rows
        if r.stripe_customer_id and r.stripe_customer_id not in SEEDED_IDS
    ]
    return rows, subs, customers


def reset(*, confirmed: bool) -> int:
    session = SessionLocal()
    try:
        rows, subs, customers = _plan(session)

        if not confirmed:
            print("DRY RUN. Nothing was changed. Re-run with --yes to apply.")
            print(f"  subscriber rows to delete:        {len(rows)}")
            print(f"  Stripe subscriptions to cancel:   {len(subs)}")
            print(f"  Stripe customers to delete:       {len(customers)}")
            for row in rows:
                print(f"    - {row.email:34} {row.status:11} {row.stripe_subscription_id or '-'}")
            return 0

        for subscription_id in subs:
            try:
                status = stripe_client.cancel_subscription(subscription_id)
                print(f"  cancelled {subscription_id} -> {status}")
            except stripe_client.StripeNotConfigured as exc:
                print(f"  SKIPPED {subscription_id}: {exc}")
            except Exception as exc:  # noqa: BLE001 - one bad id must not abort the reset
                # Already-cancelled and unknown ids both land here. Report and continue:
                # a half-finished reset is worse than a noisy one.
                print(f"  could not cancel {subscription_id}: {type(exc).__name__}")

        for customer_id in customers:
            try:
                gone = stripe_client.delete_customer(customer_id)
                print(f"  {'deleted' if gone else 'no such'} customer {customer_id}")
            except stripe_client.StripeNotConfigured as exc:
                print(f"  SKIPPED {customer_id}: {exc}")
            except Exception as exc:  # noqa: BLE001 - same reasoning as above
                print(f"  could not delete {customer_id}: {type(exc).__name__}")

        deleted = len(rows)
        for row in rows:
            session.delete(row)
        session.commit()
        print(f"  deleted {deleted} subscriber row(s)")
    finally:
        session.close()

    outcome = seed()
    print(f"  demo account {outcome}: {DEMO_EMAIL}")
    return 0


if __name__ == "__main__":
    sys.exit(reset(confirmed="--yes" in sys.argv))
