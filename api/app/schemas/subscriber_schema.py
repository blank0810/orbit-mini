from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, computed_field


# This is the only shape the dashboard ever sees; it has no password field to accidentally populate.
class SubscriberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    plan_name: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
