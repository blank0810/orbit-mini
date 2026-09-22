"""Required tests 2, 3 and 4, plus the paths that have already broken once.

Two of these cannot be produced by hand at any price. Stripe will never send a
badly-signed payload, and it cannot be told to redeliver on demand. Forging both is the
only way that code ever runs.
"""

import time

from sqlalchemy import func, select

from app.models.subscriber_model import Subscriber
from tests.conftest import post_webhook, register


def _subscriber_id(client) -> str:
    return register(client, "nina@example.com").json()["id"]


def _checkout_event(subscriber_id: str, event_id: str = "evt_1") -> dict:
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_1",
                "client_reference_id": subscriber_id,
                "customer": "cus_1",
                "subscription": "sub_1",
            }
        },
    }


# --- required 2 -------------------------------------------------------------------


def test_valid_signature_marks_the_subscriber_active(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)

    response = post_webhook(client, _checkout_event(subscriber_id))

    assert response.status_code == 200
    subscriber = db.scalar(select(Subscriber))
    assert subscriber.status == "active"
    assert subscriber.stripe_subscription_id == "sub_1"
    assert subscriber.last_stripe_event_id == "evt_1"


# --- required 3 -------------------------------------------------------------------


def test_invalid_signature_is_rejected_and_writes_nothing(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)

    response = post_webhook(client, _checkout_event(subscriber_id), secret="whsec_wrong")

    assert response.status_code == 400
    subscriber = db.scalar(select(Subscriber))
    # "writes nothing" is the real assertion. Returning 400 after already updating the row
    # would satisfy a careless test and still be an open write endpoint.
    assert subscriber.status == "incomplete"
    assert subscriber.last_stripe_event_id is None
    assert subscriber.stripe_subscription_id is None


def test_missing_signature_header_is_rejected(client, stub_stripe):
    response = client.post("/api/webhooks/stripe", content=b"{}")
    assert response.status_code == 400


# --- required 4 -------------------------------------------------------------------


def test_replayed_event_is_idempotent(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)
    event = _checkout_event(subscriber_id)

    first = post_webhook(client, event)
    subscriber = db.scalar(select(Subscriber))
    before = (
        subscriber.status,
        subscriber.stripe_subscription_id,
        subscriber.stripe_customer_id,
        subscriber.current_period_end,
        subscriber.last_stripe_event_id,
    )

    second = post_webhook(client, event)
    db.expire_all()
    subscriber = db.scalar(select(Subscriber))
    after = (
        subscriber.status,
        subscriber.stripe_subscription_id,
        subscriber.stripe_customer_id,
        subscriber.current_period_end,
        subscriber.last_stripe_event_id,
    )

    assert first.status_code == 200
    # A duplicate must still answer 2xx. Anything else and Stripe retries forever.
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert before == after, "a replayed delivery changed the row"
    assert db.scalar(select(func.count()).select_from(Subscriber)) == 1


# --- paths that have already broken once ------------------------------------------


def test_checkout_completion_records_the_billing_period(client, db, stub_stripe):
    """Regression: a Checkout session carries no period, so this used to stay NULL.

    The dashboard showed Active with a blank renewal date after a real payment.
    """
    subscriber_id = _subscriber_id(client)

    post_webhook(client, _checkout_event(subscriber_id))

    subscriber = db.scalar(select(Subscriber))
    assert subscriber.current_period_end is not None
    assert "sub_1" in stub_stripe["subscription"], "the subscription was never fetched"


def test_subscription_created_sets_status_and_period(client, db, stub_stripe):
    """created matters as much as updated: it is what Stripe fires for a new subscription."""
    subscriber_id = _subscriber_id(client)
    post_webhook(client, _checkout_event(subscriber_id))

    post_webhook(
        client,
        {
            "id": "evt_2",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "past_due",
                    "current_period_end": int(time.time()) + 2_592_000,
                }
            },
        },
    )

    assert db.scalar(select(Subscriber)).status == "past_due"


def test_subscription_deleted_cancels(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)
    post_webhook(client, _checkout_event(subscriber_id))

    post_webhook(
        client,
        {
            "id": "evt_3",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "customer": "cus_1"}},
        },
    )

    assert db.scalar(select(Subscriber)).status == "canceled"


def test_unknown_event_type_is_acknowledged_and_writes_nothing(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)

    response = post_webhook(
        client,
        {"id": "evt_x", "type": "invoice.payment_succeeded", "data": {"object": {"id": "in_1"}}},
    )

    # Not an error. A non-2xx here would make Stripe retry an event we simply ignore.
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"
    assert db.scalar(select(Subscriber)).last_stripe_event_id is None
    assert subscriber_id  # the row exists and was untouched


def test_event_for_an_unknown_subscriber_is_ignored(client, db, stub_stripe):
    register(client, "nina@example.com")

    response = post_webhook(
        client,
        {
            "id": "evt_y",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_nobody", "customer": "cus_nobody", "status": "active"}},
        },
    )

    # Stripe sends events for the whole account, including customers we do not have.
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert db.scalar(select(Subscriber)).status == "incomplete"


def test_unmapped_stripe_status_leaves_the_row_unchanged(client, db, stub_stripe):
    subscriber_id = _subscriber_id(client)
    post_webhook(client, _checkout_event(subscriber_id))

    post_webhook(
        client,
        {
            "id": "evt_4",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_1", "customer": "cus_1", "status": "some_new_status"}},
        },
    )

    # Guessing at a status Stripe invented later would be worse than leaving it alone.
    assert db.scalar(select(Subscriber)).status == "active"
