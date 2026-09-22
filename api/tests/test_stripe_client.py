"""Tests for the inside of `stripe_client`.

Every other test file stubs `stripe_client`'s *functions*, which is what keeps the suite
offline. The cost is that nothing exercises the module's own body, and that is precisely
where two production 500s have come from: `stripe.Event` and `stripe.Subscription` are not
mappings in stripe-python 15.x, and both were probed with `.get()`.

So these tests stub one level lower -- at `stripe.Subscription.retrieve` / `.modify` --
and hand back **real StripeObject instances** built with `construct_from`, which is a local
constructor and makes no network call. Returning plain dicts here would defeat the whole
point: a dict has `.get()`, so the test would pass while production kept failing.
"""

from __future__ import annotations

from typing import Any

import pytest
import stripe
from stripe._stripe_object import StripeObject

from app.services import stripe_client


def _subscription(sub_id: str = "sub_live", *, items: bool = True) -> StripeObject:
    """A Subscription shaped the way the API returns one."""
    data: dict[str, Any] = {
        "id": sub_id,
        "object": "subscription",
        "status": "active",
        "items": {
            "object": "list",
            "data": ([{"id": "si_existing", "object": "subscription_item"}] if items else []),
        },
    }
    return StripeObject.construct_from(data, "sk_test_not_a_real_key")


@pytest.fixture(autouse=True)
def _api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_require_key` raises without configuration; these tests are not about that."""
    monkeypatch.setattr(stripe_client, "_require_key", lambda: "sk_test_not_a_real_key")


def test_change_price_reads_the_item_off_a_real_stripe_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The regression. A Subscription has __getitem__ but no .get().

    Before the fix this raised:
        AttributeError: 'get' is a dict method, but a Subscription is not a dict.
    """
    captured: dict[str, Any] = {}

    def fake_retrieve(subscription_id: str, **kwargs: Any) -> StripeObject:
        return _subscription(subscription_id)

    def fake_modify(subscription_id: str, **kwargs: Any) -> StripeObject:
        captured.update(kwargs)
        captured["id"] = subscription_id
        return _subscription(subscription_id)

    monkeypatch.setattr(stripe.Subscription, "retrieve", fake_retrieve)
    monkeypatch.setattr(stripe.Subscription, "modify", fake_modify)

    result = stripe_client.change_subscription_price("sub_live", "price_new")

    assert isinstance(result, dict)
    # The EXISTING item is repointed. Sending items without an id would delete the item
    # and add another, which Stripe bills as a cancel-and-resubscribe.
    assert captured["items"] == [{"id": "si_existing", "price": "price_new"}]
    # Without this the customer is charged a full second month on the spot.
    assert captured["proration_behavior"] == "create_prorations"


def test_change_price_on_a_subscription_with_no_items_is_not_a_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No billable item means there is nothing to repoint. The caller maps this to 409."""
    monkeypatch.setattr(
        stripe.Subscription,
        "retrieve",
        lambda subscription_id, **kwargs: _subscription(subscription_id, items=False),
    )

    with pytest.raises(stripe_client.SubscriptionNotFound):
        stripe_client.change_subscription_price("sub_empty", "price_new")


def test_change_price_on_an_unknown_subscription_raises_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A subscription Stripe has never heard of is a 409, never a 500.

    The message must not carry the api key, which is why the client re-raises its own
    exception rather than letting Stripe's surface.
    """

    def fake_retrieve(subscription_id: str, **kwargs: Any) -> StripeObject:
        raise stripe.InvalidRequestError("No such subscription", param="id")

    monkeypatch.setattr(stripe.Subscription, "retrieve", fake_retrieve)

    with pytest.raises(stripe_client.SubscriptionNotFound) as excinfo:
        stripe_client.change_subscription_price("sub_missing", "price_new")

    assert "sk_test" not in str(excinfo.value)


def test_retrieve_subscription_returns_a_plain_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Callers walk this structure, so no Stripe type may leak out of the module."""
    monkeypatch.setattr(
        stripe.Subscription,
        "retrieve",
        lambda subscription_id, **kwargs: _subscription(subscription_id),
    )

    result = stripe_client.retrieve_subscription("sub_live")

    assert type(result) is dict
    assert result["items"]["data"][0]["id"] == "si_existing"
