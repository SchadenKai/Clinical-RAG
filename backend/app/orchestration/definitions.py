"""Dagster code location for the RAG batch pipelines.

Start the local UI from the ``backend`` directory:

    uv run dagster dev

Run the full pipeline headlessly:

    uv run dagster job execute -j rag_pipeline_job
"""

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)

from app.orchestration.assets import (
    evaluation_report,
    golden_dataset,
    indexed_documents,
)

# Programmatic selection (not the "*" string DSL): a transitively-pinned
# antlr4 runtime is incompatible with Dagster's selection-string parser, so we
# avoid that code path entirely.
rag_pipeline_job = define_asset_job(
    name="rag_pipeline_job", selection=AssetSelection.all()
)

# Weekly full refresh: re-index, regenerate goldens, re-evaluate. Registered in
# a STOPPED state — start it from the Dagster UI when you want it running.
weekly_rag_refresh = ScheduleDefinition(
    name="weekly_rag_refresh",
    job=rag_pipeline_job,
    cron_schedule="0 3 * * 1",
)

defs = Definitions(
    assets=[indexed_documents, golden_dataset, evaluation_report],
    jobs=[rag_pipeline_job],
    schedules=[weekly_rag_refresh],
)
