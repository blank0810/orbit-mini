"""Test fixtures.

Two rules shape everything here.

A REAL Postgres, never a mocked ORM. Mocks agree with whatever you assert, which is how a
duplicate unique constraint survived review in this very schema. The schema is built by
running the Alembic migrations, so every test run also proves the deploy path still works.

Stripe is stubbed at ONE point. `stripe_client` is the only module that imports `stripe`,
so replacing its functions takes the whole suite offline. That single seam is what makes
the forged-signature and replay tests possible at all.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

API_ROOT = Path(__file__).resolve().parent.parent

# Set before any app import: config.py is lru_cached and db/session.py builds its engine at
# import time, so both read whatever is in the environment at that moment.


def _database_url_from_env_files() -> str | None:
    """Read DATABASE_URL out of whichever env file the stack is actually running with.

    Checked in deployment order: .env.prod wins because deploying switches the database to
    its password, at which point the development .env no longer opens it. Without this the
    suite fails on a password mismatch that has nothing to do with any test.
    """
    for name in (".env.prod", ".env"):
        candidate = API_ROOT.parent / name
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                # The app runs in Docker where the host is the `db` service. From the test
                # runner on the host it is the published loopback port instead.
                return line.split("=", 1)[1].strip().replace("@db:5432", "@localhost:7303")
    return None


_default_db = (
    os.environ.get("DATABASE_URL")
    or _database_url_from_env_files()
    or "postgresql+psycopg://orbit:orbit_dev_only@localhost:7303/orbit"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", _default_db.rsplit("/", 1)[0] + "/orbit_test"
)
TEST_WEBHOOK_SECRET = "whsec_test_secret_for_the_suite"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "test-only-jwt-secret-at-least-32-characters-long"
os.environ["STRIPE_WEBHOOK_SECRET"] = TEST_WEBHOOK_SECRET
os.environ["STRIPE_SECRET_KEY"] = "sk_test_not_used_every_call_is_stubbed"
os.environ["STRIPE_PRODUCT_ID_STARTER"] = "prod_test_starter"
os.environ["STRIPE_PRODUCT_ID_PRO"] = "prod_test_pro"
os.environ["ENVIRONMENT"] = "development"
os.environ["CORS_ORIGINS"] = "http://localhost:7301"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.services import stripe_client


@pytest.fixture(scope="session")
def engine():
    """A migrated test database, separate from the one the app runs against."""
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    db_name = TEST_DATABASE_URL.rsplit("/", 1)[1]

    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()

    # Build the schema the way production does. create_all would be faster and would stop
    # the migrations from ever being exercised.
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    command.upgrade(cfg, "head")

    test_engine = create_engine(TEST_DATABASE_URL)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    """A session inside a transaction that is rolled back after every test.

    join_transaction_mode="create_savepoint" lets application code call commit() normally -
    which the controllers do - while the outer transaction still undoes everything. Without
    it each test would leak rows into the next.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Stripe stubs -----------------------------------------------------------------


class FakeCheckoutSession:
    def __init__(self, url: str = "https://checkout.stripe.com/c/pay/cs_test_fake") -> None:
        self.id = "cs_test_fake"
        self.url = url
        self.customer_id = "cus_test_fake"


@pytest.fixture
def stub_stripe(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace every outbound Stripe call. Records what was asked of it.

    construct_event is NOT stubbed: signature verification is the thing under test, so it
    runs for real against TEST_WEBHOOK_SECRET.
    """
    calls: dict[str, Any] = {
        "checkout": [],
        "price": [],
        "subscription": [],
        "change": [],
        "cancel": [],
    }

    def fake_checkout(**kwargs: Any) -> FakeCheckoutSession:
        calls["checkout"].append(kwargs)
        return FakeCheckoutSession()

    def fake_price(product_id: str) -> str:
        calls["price"].append(product_id)
        return f"price_for_{product_id}"

    def fake_subscription(subscription_id: str) -> dict[str, Any]:
        calls["subscription"].append(subscription_id)
        return {
            "id": subscription_id,
            "status": "active",
            "current_period_end": int(time.time()) + 2_592_000,
        }

    def fake_change(subscription_id: str, new_price_id: str) -> dict[str, Any]:
        calls["change"].append((subscription_id, new_price_id))
        return {"id": subscription_id, "status": "active"}

    def fake_cancel(subscription_id: str, *, cancel: bool) -> dict[str, Any]:
        calls["cancel"].append((subscription_id, cancel))
        return {"id": subscription_id, "status": "active", "cancel_at_period_end": cancel}

    monkeypatch.setattr(stripe_client, "change_subscription_price", fake_change)
    monkeypatch.setattr(stripe_client, "set_cancel_at_period_end", fake_cancel)
    monkeypatch.setattr(stripe_client, "create_checkout_session", fake_checkout)
    monkeypatch.setattr(stripe_client, "resolve_price_id", fake_price)
    monkeypatch.setattr(stripe_client, "retrieve_subscription", fake_subscription)
    return calls


# --- helpers ----------------------------------------------------------------------


def sign_payload(payload: bytes, secret: str = TEST_WEBHOOK_SECRET) -> str:
    """Produce a Stripe-Signature header the real verifier accepts.

    Stripe signs `timestamp.payload` with HMAC-SHA256. Forging one is the only way to
    exercise the webhook at all, and forging a WRONG one is the only way to prove the
    rejection path runs.
    """
    timestamp = int(time.time())
    signed = f"{timestamp}.".encode() + payload
    signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def post_webhook(client: TestClient, event: dict[str, Any], *, secret: str | None = None):
    payload = json.dumps(event).encode()
    return client.post(
        "/api/webhooks/stripe",
        content=payload,
        headers={
            "Stripe-Signature": sign_payload(payload, secret or TEST_WEBHOOK_SECRET),
            "Content-Type": "application/json",
        },
    )


def register(
    client: TestClient, email: str = "nina@example.com", password: str = "correct-horse-9"
):
    return client.post(
        "/api/auth/register",
        json={
            "first_name": "Nina",
            "last_name": "Reyes",
            "email": email,
            "password": password,
        },
    )
