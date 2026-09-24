from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

# Vercel freezes instances between requests. Close each database connection after use;
# Neon's pooled endpoint manages the server-side connection count.
engine = create_engine(get_settings().database_url, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Injected session, as a type alias. Annotated keeps Depends out of argument defaults, which
# is both the current FastAPI idiom and what ruff B008 asks for.
DbSession = Annotated[Session, Depends(get_session)]
