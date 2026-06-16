"""Run the evaluation pipeline against the golden dataset.

Usage:
    cd backend && uv run python -m app.scripts.evaluate
"""

from app.logger import app_logger
from app.pipelines.evaluation import EvalPipeline


def main() -> None:
    report = EvalPipeline.from_manual().run()
    app_logger.info(
        "Evaluation done: scored %d/%d goldens -> %s",
        report.evaluated_count,
        report.total_goldens,
        report.report_path,
    )


if __name__ == "__main__":
    main()
