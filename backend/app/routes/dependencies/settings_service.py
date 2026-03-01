from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.routes.dependencies.db_session import get_db
from app.services.settings_service import SettingsService


def get_settings_service(db: Annotated[Session, Depends(get_db)]) -> SettingsService:
    """
    FastAPI dependency defining the SettingsService injection.
    """
    return SettingsService(db=db)
