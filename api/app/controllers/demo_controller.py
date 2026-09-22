from fastapi import APIRouter, HTTPException, Response

from app.core.dependencies import set_session_cookie
from app.db.session import DbSession
from app.schemas.demo_schema import DemoAccountResponse
from app.services import demo_service

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/generate", status_code=201, response_model=DemoAccountResponse)
def generate_demo_account(response: Response, session: DbSession) -> DemoAccountResponse:
    """Create a throwaway demo account and sign the caller straight into it.

    Deliberately unauthenticated: the point is that a reviewer can click one button and be
    looking at a populated dashboard. The blast radius is bounded by the cap in
    demo_service, which evicts the oldest disposable row rather than letting the table grow.

    Known and accepted: there is no rate limiting, so this can be called repeatedly. The
    cost of that is churn among at most five throwaway rows. It can never create a sixth,
    and it can never delete the advertised demo account or a real customer.
    """
    try:
        subscriber, password, _evicted = demo_service.generate(session)
    except demo_service.UnknownDemoStatus:
        raise HTTPException(status_code=422, detail="Unknown demo status") from None
    session.commit()
    set_session_cookie(response, subscriber.id)
    return DemoAccountResponse(
        email=subscriber.email,
        password=password,
        full_name=f"{subscriber.first_name} {subscriber.last_name}",
    )
