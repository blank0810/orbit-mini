"""Required test 1: sign-up creates exactly one subscriber and returns a Checkout URL.

The brief predates accounts, so signing up is now two acts: register creates the person,
checkout sells them the plan. Both halves are asserted here.
"""

from sqlalchemy import func, select

from app.models.subscriber_model import Subscriber
from tests.conftest import register


def test_register_creates_exactly_one_subscriber(client, db):
    response = register(client, "nina@example.com")

    assert response.status_code == 201
    # "exactly one" is the assertion that matters. A signup creating two rows still looks
    # fine to the person using it and only breaks later, when the webhook cannot tell
    # which row to activate.
    assert db.scalar(select(func.count()).select_from(Subscriber)) == 1

    body = response.json()
    assert body["email"] == "nina@example.com"
    assert body["status"] == "incomplete", "a new account has not paid yet"
    assert "password" not in body and "password_hash" not in body


def test_checkout_returns_a_stripe_url_and_does_not_create_a_second_row(client, db, stub_stripe):
    register(client, "nina@example.com")

    response = client.post("/api/checkout", json={"plan": "starter"})

    assert response.status_code == 200
    assert response.json()["checkout_url"].startswith("https://checkout.stripe.com/")
    assert db.scalar(select(func.count()).select_from(Subscriber)) == 1

    # The subscriber id must travel with the session: it is the only thing that maps a
    # completed Checkout back to our row.
    subscriber = db.scalar(select(Subscriber))
    assert stub_stripe["checkout"][0]["subscriber_id"] == subscriber.id


def test_checkout_requires_authentication(client):
    assert client.post("/api/checkout", json={"plan": "starter"}).status_code == 401


def test_plan_name_is_written_from_the_server_side_catalogue(client, db, stub_stripe):
    register(client, "nina@example.com")
    client.post("/api/checkout", json={"plan": "pro"})

    subscriber = db.scalar(select(Subscriber))
    # Never taken from the request, so the stored name cannot disagree with what was charged.
    assert subscriber.plan_name == "ScaleSage Pro"
