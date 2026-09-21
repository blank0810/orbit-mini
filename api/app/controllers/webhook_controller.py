import logging

from fastapi import APIRouter, HTTPException, Request

from app.db.session import DbSession
from app.services import stripe_client, webhook_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Deliberately no session authentication: the signature IS the authentication,
# and Stripe cannot present a session cookie.
@router.post("/stripe", status_code=200)
async def stripe_webhook(request: Request, session: DbSession) -> dict[str, str]:
    # The signature covers the exact bytes Stripe sent; parsing JSON first and
    # re-serialising would break verification.
    payload = await request.body()
    signature_header = request.headers.get("Stripe-Signature")
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe_client.construct_event(payload, signature_header)
    except stripe_client.InvalidWebhookSignature:
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    except stripe_client.StripeNotConfigured:
        # Misconfiguration is our fault, not malformed delivery; report a server failure
        # so Stripe can retry after configuration is fixed rather than burn its retries.
        raise HTTPException(status_code=503, detail="Webhook is not configured") from None

    outcome = webhook_service.apply_event(session, event)
    session.commit()
    logger.info("Stripe event id=%s type=%s outcome=%s", event["id"], event["type"], outcome)
    # Anything other than 2xx makes Stripe retry, so duplicates and unknowns still get 200.
    return {"status": outcome}
