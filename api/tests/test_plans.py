"""The plan key is a closed set, not a passthrough."""

import pytest

from tests.conftest import register


def test_plans_are_public_and_expose_no_stripe_ids(client):
    response = client.get("/api/plans")

    assert response.status_code == 200
    assert {p["key"] for p in response.json()} == {"starter", "pro"}
    # A product or price id here would let a caller name a price directly.
    assert "prod_" not in response.text
    assert "price_" not in response.text


def test_exactly_one_plan_is_recommended(client):
    recommended = [p for p in client.get("/api/plans").json() if p["recommended"]]
    # Two ranked options is a decision. Two equal ones is a comparison task.
    assert len(recommended) == 1
    assert recommended[0]["key"] == "pro"


@pytest.mark.parametrize(
    "plan",
    ["enterprise", "price_1UI77NGaiYVONt3BVfvZ70Kg", "prod_VIiYndmcFisPhz", "", "starter "],
)
def test_checkout_rejects_anything_outside_the_closed_set(client, stub_stripe, plan):
    register(client, "nina@example.com")

    response = client.post("/api/checkout", json={"plan": plan})

    # 422 before Stripe is ever called. A raw price id must never reach the API as a plan.
    assert response.status_code == 422
    assert stub_stripe["checkout"] == []


def test_changing_to_the_plan_already_held_is_refused(client, db, stub_stripe):
    register(client, "nina@example.com")
    client.post("/api/checkout", json={"plan": "pro"})
    from sqlalchemy import select

    from app.models.subscriber_model import Subscriber

    subscriber = db.scalar(select(Subscriber))
    subscriber.status = "active"
    subscriber.stripe_subscription_id = "sub_1"
    db.flush()

    response = client.post("/api/subscription/change", json={"plan": "pro"})
    assert response.status_code == 409


def test_changing_plan_without_a_subscription_is_refused(client, stub_stripe):
    register(client, "nina@example.com")

    response = client.post("/api/subscription/change", json={"plan": "pro"})

    # Never a 500: no subscription is a conflict with our own state.
    assert response.status_code == 409
