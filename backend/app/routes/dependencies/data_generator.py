from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.settings import get_app_settings
from app.services.evaluation.dataset import SyntheticDataGenerator
from app.services.file_store.db import S3Service


@lru_cache
def get_synthetic_data_generator(
    settings: Annotated[Settings, Depends(get_app_settings)],
    s3_service: Annotated[S3Service, Depends(get_s3_service)],
) -> SyntheticDataGenerator:
    return SyntheticDataGenerator(settings=settings, s3_service=s3_service)
