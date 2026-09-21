from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentSubscriber
from app.db.session import DbSession
from app.schemas.checkout_schema import CheckoutRequest, CheckoutResponse, PlanRead
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


@router.get("/plans", response_model=list[PlanRead])
def list_plans() -> list[PlanRead]:
    # Public pricing needs no login. Expose only presentation fields, never product or price ids.
    return [
        PlanRead(key=plan.key, display_name=plan.display_name, recommended=plan.recommended)
        for plan in plan_catalogue.get_plans().values()
    ]
