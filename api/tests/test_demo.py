"""The demo cap, and the guarantee that it cannot reach anyone real."""

from sqlalchemy import func, select

from app.models.subscriber_model import Subscriber
from app.services import demo_service
from tests.conftest import register


def _disposable_count(db) -> int:
    return db.scalar(
        select(func.count()).select_from(Subscriber).where(Subscriber.is_disposable.is_(True))
    )


def test_generate_creates_a_signed_in_disposable_account(client, db):
    response = client.post("/api/demo/generate")

    assert response.status_code == 201
    body = response.json()
    assert body["email"].startswith("demo-")
    # The cookie is set on this response, so the caller is already signed in.
    assert client.get("/api/subscribers/me").json()["email"] == body["email"]
    assert _disposable_count(db) == 1


def test_the_cap_holds_however_many_times_it_is_pressed(client, db):
    for _ in range(demo_service.MAX_DISPOSABLE + 4):
        assert client.post("/api/demo/generate").status_code == 201

    assert _disposable_count(db) == demo_service.MAX_DISPOSABLE


def test_eviction_removes_the_oldest_first(client, db):
    first = client.post("/api/demo/generate").json()["email"]
    for _ in range(demo_service.MAX_DISPOSABLE):
        client.post("/api/demo/generate")

    remaining = {s.email for s in db.scalars(select(Subscriber))}
    assert first not in remaining


def test_eviction_never_touches_a_real_customer(client, db):
    """The guarantee that matters. A paying customer must be unreachable by the cap."""
    register(client, "real.customer@example.com")

    for _ in range(demo_service.MAX_DISPOSABLE + 3):
        client.post("/api/demo/generate")

    survivors = {s.email for s in db.scalars(select(Subscriber))}
    assert "real.customer@example.com" in survivors
    assert _disposable_count(db) == demo_service.MAX_DISPOSABLE


def test_eviction_never_touches_a_non_disposable_demo(client, db):
    """The advertised account is not flagged, so the printed credentials cannot go stale."""
    advertised = Subscriber(
        email="demo@orbit.ehnand.com",
        first_name="Demo",
        last_name="Account",
        password_hash="x",
        plan_name="ScaleSage Pro",
        status="active",
        is_disposable=False,
    )
    db.add(advertised)
    db.flush()

    for _ in range(demo_service.MAX_DISPOSABLE + 3):
        client.post("/api/demo/generate")

    survivors = {s.email for s in db.scalars(select(Subscriber))}
    assert "demo@orbit.ehnand.com" in survivors


def test_generated_accounts_carry_fake_stripe_ids(client, db):
    client.post("/api/demo/generate")

    subscriber = db.scalar(select(Subscriber).where(Subscriber.is_disposable.is_(True)))
    # Must never be mistakable for evidence that a real payment was recorded.
    assert subscriber.stripe_subscription_id == "sub_demo_generated"
    assert subscriber.stripe_customer_id == "cus_demo_generated"
