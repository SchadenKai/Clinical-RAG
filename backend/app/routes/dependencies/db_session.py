from typing import Iterator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency that provides a database session.
    It yields a session from the session factory (`SessionLocal`) and ensures
    it is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
