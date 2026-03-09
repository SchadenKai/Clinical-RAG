from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.services.file_store.db import S3Service


class AgentContext(BaseModel):
    s3_service: S3Service
    settings: Settings

    model_config = ConfigDict(arbitrary_types_allowed=True)
