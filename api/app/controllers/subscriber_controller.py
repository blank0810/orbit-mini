from fastapi import APIRouter

from app.core.dependencies import CurrentSubscriber
from app.models.subscriber_model import Subscriber
from app.schemas.subscriber_schema import SubscriberRead

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.get("/me", status_code=200, response_model=SubscriberRead)
def me(subscriber: CurrentSubscriber) -> Subscriber:
    # The dependency already loaded this subscriber; a second lookup has no purpose.
    return subscriber
