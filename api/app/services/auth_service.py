from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriber_model import Subscriber
from app.repositories import subscriber_repository
from app.schemas.auth_schema import RegisterRequest

_hasher = PasswordHash.recommended()
# Precompute once so unknown accounts still pay the same password verification cost.
_dummy_hash = _hasher.hash("orbit-dummy-password-for-timing")


class EmailAlreadyRegistered(Exception):
    pass


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(plain, hashed)
    except Exception:  # noqa: BLE001 - deliberately broad
        # A corrupt, truncated or unknown-algorithm hash must fail authentication, not 500.
        # Narrowing this would let an unexpected hasher error surface as a server error and
        # tell an attacker that this particular account is stored differently.
        return False


def create_access_token(subscriber_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(subscriber_id),
            "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
            "iat": now,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> UUID | None:
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"]},
        )
        return UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return None


def register_subscriber(session: Session, data: RegisterRequest) -> Subscriber:
    if subscriber_repository.get_by_email(session, str(data.email)) is not None:
        raise EmailAlreadyRegistered

    subscriber = Subscriber(
        email=str(data.email),
        first_name=data.first_name,
        last_name=data.last_name,
        password_hash=hash_password(data.password),
        plan_name=get_settings().plan_name,
        status="incomplete",
    )
    return subscriber_repository.create(session, subscriber)


def authenticate(session: Session, email: str, password: str) -> Subscriber | None:
    subscriber = subscriber_repository.get_by_email(session, email)
    hashed = subscriber.password_hash if subscriber is not None else _dummy_hash
    password_matches = verify_password(password, hashed)
    # Identical failure for unknown email and wrong password, by design.
    if subscriber is None or not password_matches:
        return None
    return subscriber
