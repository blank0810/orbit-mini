from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response

from app.core.config import get_settings
from app.db.session import DbSession
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.services.auth_service import create_access_token, decode_access_token


def get_current_subscriber(request: Request, session: DbSession) -> Subscriber:
    token = request.cookies.get(get_settings().cookie_name)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    subscriber_id = decode_access_token(token)
    if subscriber_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    subscriber = subscriber_repository.get_by_id(session, subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return subscriber


CurrentSubscriber = Annotated[Subscriber, Depends(get_current_subscriber)]


def set_session_cookie(response: Response, subscriber_id: UUID) -> None:
    """Write the session cookie. Lives beside the reader so both agree on every flag."""
    settings = get_settings()
    # SameSite must be lax, not strict: Stripe Checkout returns via a cross-site top-level
    # navigation. Strict would drop the cookie and silently log the user out mid-purchase.
    response.set_cookie(
        key=settings.cookie_name,
        value=create_access_token(subscriber_id),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
