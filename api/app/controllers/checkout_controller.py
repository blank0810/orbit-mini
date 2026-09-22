from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentSubscriber
from app.db.session import DbSession
from app.models.subscriber_model import Subscriber
from app.schemas.checkout_schema import (
    ChangePlanRequest,
    ChangePlanResponse,
    CheckoutRequest,
    CheckoutResponse,
    PlanRead,
)
from app.schemas.subscriber_schema import SubscriberRead
from app.services import plan_catalogue, stripe_client, subscription_service

router = APIRouter(tags=["checkout"])


@router.post("/checkout", status_code=200, response_model=CheckoutResponse)
def checkout(
    data: CheckoutRequest, session: DbSession, subscriber: CurrentSubscriber
) -> CheckoutResponse:
    try:
        checkout_url = subscription_service.start_checkout(session, subscriber, data.plan)
    except plan_catalogue.UnknownPlan:
        raise HTTPException(status_code=422, detail="Unknown plan") from None
    except subscription_service.AlreadySubscribed:
        raise HTTPException(
            status_code=409, detail="You already have an active subscription"
        ) from None
    except stripe_client.StripeNotConfigured:
        raise HTTPException(status_code=503, detail="Payments are not configured") from None
    session.commit()
    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/subscription/change", status_code=200, response_model=ChangePlanResponse)
def change_plan(
    data: ChangePlanRequest, session: DbSession, subscriber: CurrentSubscriber
) -> ChangePlanResponse:
    """Move a live subscription to the other plan, prorated.

    Separate from /checkout on purpose: checking out again would open a second Stripe
    subscription and bill the customer twice.
    """
    try:
        plan_name = subscription_service.change_plan(session, subscriber, data.plan)
    except plan_catalogue.UnknownPlan:
        raise HTTPException(status_code=422, detail="Unknown plan") from None
    except subscription_service.NotSubscribed:
        raise HTTPException(
            status_code=409, detail="You do not have an active subscription to change"
        ) from None
    except subscription_service.AlreadyOnPlan:
        raise HTTPException(status_code=409, detail="You are already on that plan") from None
    except stripe_client.SubscriptionNotFound:
        # Demo rows carry fake subscription ids on purpose. That is a conflict with our own
        # state, not a payments outage, so it is a 409 rather than a 500 or a 503.
        raise HTTPException(status_code=409, detail="This subscription cannot be changed") from None
    except stripe_client.StripeNotConfigured:
        raise HTTPException(status_code=503, detail="Payments are not configured") from None
    session.commit()
    return ChangePlanResponse(plan_name=plan_name)


@router.post("/subscription/cancel", status_code=200, response_model=SubscriberRead)
def cancel_subscription(session: DbSession, subscriber: CurrentSubscriber) -> Subscriber:
    """Schedule cancellation for the end of the period already paid for."""
    try:
        subscription_service.cancel(session, subscriber)
    except subscription_service.NotCancellable:
        raise HTTPException(
            status_code=409, detail="You do not have a subscription to cancel"
        ) from None
    except stripe_client.SubscriptionNotFound:
        raise HTTPException(status_code=409, detail="This subscription cannot be changed") from None
    except stripe_client.StripeNotConfigured:
        raise HTTPException(status_code=503, detail="Payments are not configured") from None
    session.commit()
    return subscriber


@router.post("/subscription/resume", status_code=200, response_model=SubscriberRead)
def resume_subscription(session: DbSession, subscriber: CurrentSubscriber) -> Subscriber:
    """Call off a scheduled cancellation while the period is still running."""
    try:
        subscription_service.resume(session, subscriber)
    except subscription_service.NotCancellable:
        raise HTTPException(
            status_code=409, detail="You do not have a subscription to resume"
        ) from None
    except stripe_client.SubscriptionNotFound:
        raise HTTPException(status_code=409, detail="This subscription cannot be changed") from None
    except stripe_client.StripeNotConfigured:
        raise HTTPException(status_code=503, detail="Payments are not configured") from None
    session.commit()
    return subscriber


@router.get("/plans", response_model=list[PlanRead])
def list_plans() -> list[PlanRead]:
    # Public pricing needs no login. Expose only presentation fields, never product or price ids.
    return [
        PlanRead(key=plan.key, display_name=plan.display_name, recommended=plan.recommended)
        for plan in plan_catalogue.get_plans().values()
    ]
