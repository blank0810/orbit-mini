from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_session

router = APIRouter()

# Liveness ignores the database so a database blip does not make a live process look dead.
# Readiness checks the database because serving requests requires it.


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", response_model=None)
def readiness(session: Annotated[Session, Depends(get_session)]) -> dict[str, str] | JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except (
        SQLAlchemyError
    ):  # any database failure means not ready; nothing else should be swallowed
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}
