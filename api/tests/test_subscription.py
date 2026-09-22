"""Switching plans in either direction, and cancelling without losing paid time."""

import pytest
from sqlalchemy import select

from app.models.subscriber_model import Subscriber
from tests.conftest import post_webhook, register


@pytest.fixture
def active_subscriber(client, db, stub_stripe):
    """A subscriber with a live subscription, arrived at the way a real one does."""
    subscriber_id = register(client, "nina@example.com").json()["id"]
    client.post("/api/checkout", json={"plan": "pro"})
    post_webhook(
        client,
        {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_1",
                    "client_reference_id": subscriber_id,
                    "customer": "cus_1",
                    "subscription": "sub_1",
                }
            },
        },
    )
    db.expire_all()
    return db.scalar(select(Subscriber))


# --- switching, both directions ---------------------------------------------------


def test_downgrade_pro_to_starter(client, db, active_subscriber, stub_stripe):
    response = client.post("/api/subscription/change", json={"plan": "starter"})

    assert response.status_code == 200
    assert response.json()["plan_name"] == "ScaleSage Starter"
    db.expire_all()
    assert db.scalar(select(Subscriber)).plan_name == "ScaleSage Starter"
    # Repointed, never re-checked-out: a second checkout would open a second subscription.
    assert stub_stripe["change"] == [("sub_1", "price_for_prod_test_starter")]
    assert len(stub_stripe["checkout"]) == 1


def test_upgrade_starter_to_pro(client, db, active_subscriber, stub_stripe):
    client.post("/api/subscription/change", json={"plan": "starter"})
    stub_stripe["change"].clear()

    response = client.post("/api/subscription/change", json={"plan": "pro"})

    assert response.status_code == 200
    assert response.json()["plan_name"] == "ScaleSage Pro"
    assert stub_stripe["change"] == [("sub_1", "price_for_prod_test_pro")]


# --- cancelling -------------------------------------------------------------------


def test_cancel_schedules_for_period_end_and_keeps_access(
    client, db, active_subscriber, stub_stripe
):
    response = client.post("/api/subscription/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["cancel_at_period_end"] is True
    # Still active. The customer paid through the end of this period and keeps it.
    assert body["status"] == "active"
    assert stub_stripe["cancel"] == [("sub_1", True)]


def test_resume_calls_the_cancellation_off(client, db, active_subscriber, stub_stripe):
    client.post("/api/subscription/cancel")
    stub_stripe["cancel"].clear()

    response = client.post("/api/subscription/resume")

    assert response.status_code == 200
    assert response.json()["cancel_at_period_end"] is False
    assert stub_stripe["cancel"] == [("sub_1", False)]


def test_cancel_without_a_subscription_is_a_conflict(client, stub_stripe):
    register(client, "nina@example.com")

    # Never a 500: nothing to cancel is a conflict with our own state.
    assert client.post("/api/subscription/cancel").status_code == 409
    assert client.post("/api/subscription/resume").status_code == 409


def test_cancel_requires_authentication(client):
    assert client.post("/api/subscription/cancel").status_code == 401


# --- Stripe stays the source of truth ---------------------------------------------


def test_webhook_mirrors_a_cancellation_made_in_stripe(client, db, active_subscriber, stub_stripe):
    """Cancelling from the Stripe dashboard must reach us too, not just our own UI."""
    post_webhook(
        client,
        {
            "id": "evt_9",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "active",
                    "cancel_at_period_end": True,
                }
            },
        },
    )

    db.expire_all()
    assert db.scalar(select(Subscriber)).cancel_at_period_end is True


def test_deletion_clears_the_scheduled_flag(client, db, active_subscriber, stub_stripe):
    client.post("/api/subscription/cancel")

    post_webhook(
        client,
        {
            "id": "evt_10",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "customer": "cus_1"}},
        },
    )

    db.expire_all()
    subscriber = db.scalar(select(Subscriber))
    assert subscriber.status == "canceled"
    # The scheduled cancellation has happened; leaving the flag set would make the UI
    # offer to "keep" a subscription that is already gone.
    assert subscriber.cancel_at_period_end is False
