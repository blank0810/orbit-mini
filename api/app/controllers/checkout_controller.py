from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentSubscriber
from app.db.session import DbSession
from app.schemas.checkout_schema import CheckoutResponse
from app.services import stripe_client, subscription_service

router = APIRouter(tags=["checkout"])


@router.post("/checkout", status_code=200, response_model=CheckoutResponse)
def checkout(session: DbSession, subscriber: CurrentSubscriber) -> CheckoutResponse:
    try:
        checkout_url = subscription_service.start_checkout(session, subscriber)
    except subscription_service.AlreadySubscribed:
        raise HTTPException(
            status_code=409, detail="You already have an active subscription"
        ) from None
    except stripe_client.StripeNotConfigured:
        raise HTTPException(status_code=503, detail="Payments are not configured") from None
    session.commit()
    return CheckoutResponse(checkout_url=checkout_url)
