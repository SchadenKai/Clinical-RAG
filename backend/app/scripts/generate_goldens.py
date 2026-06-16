"""Run the SDG pipeline to generate and persist the golden dataset.

Generates goldens from every document in the configured object-store bucket
and writes them to the golden-dataset artifact consumed by the eval pipeline.

Usage:
    cd backend && uv run python -m app.scripts.generate_goldens
"""

from app.logger import app_logger
from app.pipelines.sdg import SdgPipeline


def main() -> None:
    report = SdgPipeline.from_manual().run()
    app_logger.info(
        "SDG done: %d goldens written to %s",
        report.golden_count,
        report.output_path,
    )


if __name__ == "__main__":
    main()
