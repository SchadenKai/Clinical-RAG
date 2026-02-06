from typing import Annotated

from fastapi import Depends

from app.core.config import Settings
from app.routes.dependencies.settings import get_app_settings
from app.services.evaluation.evaluator import EvaluationPipeline


def get_evaluation_pipeline(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> EvaluationPipeline:
    return EvaluationPipeline(settings=settings)


def get_evaluation_pipeline_manual() -> EvaluationPipeline:
    settings = get_app_settings()
    return EvaluationPipeline(settings=settings)
