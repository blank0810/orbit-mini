from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# These mirror Stripe's subscription statuses and are never invented locally.
SUBSCRIBER_STATUSES = ("incomplete", "active", "past_due", "canceled")


class Subscriber(Base):
    """A subscriber whose known Stripe statuses are documented in SUBSCRIBER_STATUSES."""

    __tablename__ = "subscriber"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Marks a generated throwaway demo row. The system may DELETE these without asking,
    # so the flag is explicit rather than inferred from the email: a real customer who
    # happened to register a demo-looking address must never be evicted by a convention.
    # The advertised demo account is deliberately NOT flagged and so can never be evicted.
    is_disposable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Stripe keeps a cancelled subscription ACTIVE until the paid period runs out, so
    # status alone cannot tell "renews on the 21st" from "ends on the 21st". Without this
    # the dashboard would promise a renewal that is not coming.
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Idempotency guard: the last Stripe event applied to this row rejects a replayed delivery.
    last_stripe_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Subscriber(id={self.id!r}, email={self.email!r}, status={self.status!r})"
