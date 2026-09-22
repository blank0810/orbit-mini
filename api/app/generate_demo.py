"""Generate a disposable demo subscriber from the command line.

    python -m app.generate_demo                      # active, on Pro
    python -m app.generate_demo --status past_due
    python -m app.generate_demo --status incomplete --plan starter

Same code path as the button on the login page, so the five-account cap and the eviction
of the oldest apply here too. Anything else would let the CLI quietly grow the table past
the limit the UI enforces.
"""

from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.models.subscriber_model import SUBSCRIBER_STATUSES
from app.services import demo_service

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a disposable demo subscriber.")
    parser.add_argument("--status", default="active", choices=list(SUBSCRIBER_STATUSES))
    parser.add_argument("--plan", default="pro", choices=list(demo_service.PLAN_NAMES))
    args = parser.parse_args()

    session = SessionLocal()
    try:
        subscriber, password, evicted = demo_service.generate(
            session, status=args.status, plan=args.plan
        )
        session.commit()
        for address in evicted:
            print(f"  evicted:  {address}")
        print(f"  email:    {subscriber.email}")
        print(f"  password: {password}")
        print(f"  status:   {subscriber.status}")
    finally:
        session.close()
