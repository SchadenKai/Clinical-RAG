"""Synthetic data generation (SDG) pipeline.

Reads source documents from the object store, generates evaluation goldens with
deepeval, and persists them as a versioned JSON artifact that the evaluation
pipeline later consumes. Stands alone from the indexing and evaluation
pipelines and never invokes them directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from deepeval.dataset.golden import Golden

from app.logger import app_logger
from app.services.sdg import SyntheticDataGenerator

DEFAULT_GOLDENS_PATH = "app/data/reports/synthetic_golden_dataset.json"


@dataclass(frozen=True)
class SdgPipelineReport:
    golden_count: int
    output_path: str


def _golden_to_dict(golden: Golden) -> dict:
    """Serialize a deepeval Golden into the schema the eval pipeline reads."""
    if hasattr(golden, "model_dump"):
        return golden.model_dump(mode="json")
    return {
        "input": getattr(golden, "input", None),
        "expected_output": getattr(golden, "expected_output", None),
        "context": getattr(golden, "context", None),
        "additional_metadata": getattr(golden, "additional_metadata", None),
    }


class SdgPipeline:
    """Generates goldens and persists them as a reusable dataset artifact."""

    def __init__(
        self,
        generator: SyntheticDataGenerator,
        output_path: str = DEFAULT_GOLDENS_PATH,
    ):
        self._generator = generator
        self._output_path = output_path

    @classmethod
    def from_manual(cls, output_path: str = DEFAULT_GOLDENS_PATH) -> "SdgPipeline":
        from app.routes.dependencies.file_store import get_s3_service
        from app.routes.dependencies.settings import get_app_settings

        settings = get_app_settings()
        s3_service = get_s3_service(settings)
        generator = SyntheticDataGenerator(settings=settings, s3_service=s3_service)
        return cls(generator=generator, output_path=output_path)

    def run(
        self,
        file_keys: list[str] | None = None,
        max_goldens_per_context: int = 10,
    ) -> SdgPipelineReport:
        goldens = self._generator.generate(
            file_keys=file_keys,
            max_goldens_per_context=max_goldens_per_context,
        )
        serialized = [_golden_to_dict(golden) for golden in goldens]

        output_path = Path(self._output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        app_logger.info(
            "SDG pipeline persisted %d golden(s) to %s", len(serialized), output_path
        )
        return SdgPipelineReport(
            golden_count=len(serialized), output_path=str(output_path)
        )
