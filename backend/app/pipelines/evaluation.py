"""Evaluation pipeline.

Consumes the golden dataset produced by the SDG pipeline, runs each query
through the retrieval/answering agent, scores the results with deepeval RAG
metrics, and writes a Markdown report. Stands alone from the indexing and SDG
pipelines: it reads the SDG artifact and the live retriever but never invokes
those pipelines directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from deepeval.evaluate.types import EvaluationResult
from deepeval.test_case import LLMTestCase

from app.logger import app_logger
from app.services.evaluation.evaluator import EvaluationPipeline
from app.services.rag import RetrievalService
from app.utils import get_request_id

DEFAULT_GOLDENS_PATH = "app/data/reports/synthetic_golden_dataset.json"
DEFAULT_REPORT_PATH = "app/data/reports/test_report.md"
DEFAULT_QUALITY_THRESHOLD = 0.8


@dataclass(frozen=True)
class EvalPipelineReport:
    evaluation_result: EvaluationResult
    report_path: str
    evaluated_count: int
    total_goldens: int


def _format_metric_value(value: object) -> str:
    """Format scores to 3 decimal places when they are floats."""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _passes_quality(golden: dict, threshold: float) -> bool:
    meta = golden.get("additional_metadata") or {}
    return (
        meta.get("context_quality", 0) > threshold
        and meta.get("synthetic_input_quality", 0) > threshold
    )


def _generate_md_report(evaluation_result: EvaluationResult) -> str:
    """Render a deepeval EvaluationResult as a Markdown report."""
    md_output = ""

    for test_result in evaluation_result.test_results:
        icon = "✅" if test_result.success else "❌"
        status_text = "PASSED" if test_result.success else "FAILED"

        md_output += f"# 🧪 Test Case: {test_result.name}\n\n"
        md_output += f"**Status:** {icon} **{status_text}**\n\n"

        input_display = test_result.input
        if isinstance(input_display, list):
            input_display = str(input_display)
        md_output += f'**Input Query:**\n> *"{input_display}"*\n\n'
        md_output += "---\n\n"

        if test_result.metrics_data:
            md_output += "## 📊 Metrics Summary\n\n"
            md_output += "| Metric Name | Score | Threshold | Status |\n"
            md_output += "| :--- | :--- | :--- | :--- |\n"
            for metric in test_result.metrics_data:
                m_icon = "✅ Pass" if metric.success else "❌ Fail"
                score = _format_metric_value(metric.score)
                threshold = _format_metric_value(metric.threshold)
                md_output += (
                    f"| **{metric.name}** | {score} | {threshold} | {m_icon} |\n"
                )
            md_output += "\n---\n\n"

            md_output += "## 🔍 Detailed Analysis\n\n"
            for metric in test_result.metrics_data:
                m_icon = "✅" if metric.success else "❌"
                score = _format_metric_value(metric.score)
                md_output += f"### {m_icon} {metric.name}\n"
                md_output += f"- **Score:** {score}\n"
                md_output += f"- **Reason:** {metric.reason}\n\n"
                if metric.verbose_logs:
                    md_output += (
                        "<details>\n<summary><strong>View Verbose Logs"
                        " & Verdicts</strong></summary>\n\n"
                    )
                    md_output += "```text\n"
                    md_output += str(metric.verbose_logs)
                    md_output += "\n```\n"
                    md_output += "</details>\n\n"

        md_output += "## 📚 Retrieval Data\n\n"
        if test_result.retrieval_context:
            md_output += (
                "<details>\n<summary><strong>Retrieval Context"
                "(Chunks)</strong></summary>\n\n"
            )
            for i, ctx in enumerate(test_result.retrieval_context):
                md_output += f"**Chunk {i + 1}:**\n> {ctx}\n\n"
            md_output += "</details>\n\n"

        if test_result.actual_output:
            md_output += f"**Actual LLM Output:**\n\n> {test_result.actual_output}\n\n"

        md_output += "---\n\n"

    return md_output


class EvalPipeline:
    """Scores the RAG agent against the persisted golden dataset."""

    def __init__(
        self,
        retriever_service: RetrievalService,
        evaluator: EvaluationPipeline,
        goldens_path: str = DEFAULT_GOLDENS_PATH,
        report_path: str = DEFAULT_REPORT_PATH,
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    ):
        self._retriever_service = retriever_service
        self._evaluator = evaluator
        self._goldens_path = goldens_path
        self._report_path = report_path
        self._quality_threshold = quality_threshold

    @classmethod
    def from_manual(
        cls,
        goldens_path: str = DEFAULT_GOLDENS_PATH,
        report_path: str = DEFAULT_REPORT_PATH,
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    ) -> "EvalPipeline":
        from app.routes.dependencies.evaluator import get_evaluation_pipeline_manual
        from app.routes.dependencies.rag import get_retriever_service_manual

        return cls(
            retriever_service=get_retriever_service_manual(),
            evaluator=get_evaluation_pipeline_manual(),
            goldens_path=goldens_path,
            report_path=report_path,
            quality_threshold=quality_threshold,
        )

    def run(self, limit: int | None = None) -> EvalPipelineReport:
        raw_goldens = self._read_goldens_file()
        selected = self._filter_by_quality(raw_goldens)
        if limit is not None:
            selected = selected[:limit]
        if not selected:
            app_logger.warning(
                "Eval: no goldens passed quality>%.2f; report will be empty",
                self._quality_threshold,
            )

        test_cases = self._build_test_cases(selected)
        result = self._evaluator.evaluate(test_cases)

        report_path = Path(self._report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_generate_md_report(result), encoding="utf-8")
        app_logger.info("Eval: wrote report to %s", report_path)

        return EvalPipelineReport(
            evaluation_result=result,
            report_path=str(report_path),
            evaluated_count=len(test_cases),
            total_goldens=len(raw_goldens),
        )

    def _read_goldens_file(self) -> list[dict]:
        try:
            with open(self._goldens_path, encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Golden dataset not found at {self._goldens_path}. "
                "Run the SDG pipeline first (python -m app.scripts.generate_goldens)."
            ) from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Golden dataset at {self._goldens_path} is not valid JSON: {e}"
            ) from e

    def _filter_by_quality(self, goldens: list[dict]) -> list[dict]:
        threshold = self._quality_threshold
        kept = [golden for golden in goldens if _passes_quality(golden, threshold)]
        app_logger.info(
            "Eval: %d/%d goldens passed quality>%.2f",
            len(kept),
            len(goldens),
            threshold,
        )
        return kept

    def _build_test_cases(self, goldens: list[dict]) -> list[LLMTestCase]:
        test_cases: list[LLMTestCase] = []
        for golden in goldens:
            query = golden["input"]
            agent_state = self._retriever_service.retrieve_documents(
                query=query, is_llm_enabled=True, request_id=get_request_id()
            )
            retrieved_contexts = [doc["text"] for doc in agent_state["documents"]]
            test_cases.append(
                LLMTestCase(
                    input=query,
                    actual_output=agent_state["final_answer"],
                    expected_output=golden["expected_output"],
                    context=golden["context"],
                    retrieval_context=retrieved_contexts,
                )
            )
        return test_cases
