"""Dagster orchestration layer.

Thin wrappers that turn the standalone batch pipelines in ``app.pipelines`` into
Dagster software-defined assets. The pipelines remain the execution engine;
Dagster owns scheduling, lineage, retries, and run observability.

Run the local UI from the ``backend`` directory:

    uv run dagster dev

The code location is registered via ``[tool.dagster]`` in ``pyproject.toml``.
"""
