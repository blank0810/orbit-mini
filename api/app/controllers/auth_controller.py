from fastapi import APIRouter, HTTPException, Response

from app.core.config import get_settings
from app.core.dependencies import CurrentSubscriber, set_session_cookie
from app.db.session import DbSession
from app.models.subscriber_model import Subscriber
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.schemas.subscriber_schema import SubscriberRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=SubscriberRead)
def register(data: RegisterRequest, response: Response, session: DbSession) -> Subscriber:
    try:
        subscriber = auth_service.register_subscriber(session, data)
    except auth_service.EmailAlreadyRegistered:
        # KNOWN, ACCEPTED: this confirms an address has an account, so registration is an
        # enumeration oracle. Login is not - it returns an identical 401 and runs a hash
        # verification for absent accounts so timing does not leak either.
        # Closing it here needs the flow we deliberately cut: always answer 201 and send
        # mail that either welcomes you or says you already have an account. With no mail
        # system, hiding it would instead tell a real user their signup worked when it did
        # not. Rate limiting, the other mitigation, is also out of scope.
        # Reported as a gap rather than silently traded away. AGENTS.md section 12.
        raise HTTPException(status_code=409, detail="That email is already registered") from None
    session.commit()
    set_session_cookie(response, subscriber.id)
    return subscriber


@router.post("/login", status_code=200, response_model=SubscriberRead)
def login(data: LoginRequest, response: Response, session: DbSession) -> Subscriber:
    subscriber = auth_service.authenticate(session, str(data.email), data.password)
    if subscriber is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    set_session_cookie(response, subscriber.id)
    return subscriber


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


@router.get("/me", status_code=200, response_model=SubscriberRead)
def me(subscriber: CurrentSubscriber) -> Subscriber:
    return subscriber
