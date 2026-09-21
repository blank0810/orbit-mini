from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.core.config import get_settings
from app.db.session import DbSession
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.services.auth_service import decode_access_token


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
