import json

from pytest_mock import MockerFixture, MockType

from app.pipelines.evaluation import EvalPipeline
from app.services.evaluation.evaluator import EvaluationPipeline
from app.services.rag import RetrievalService


def _golden(input_text: str, ctx_q: float, input_q: float) -> dict:
    return {
        "input": input_text,
        "expected_output": f"expected for {input_text}",
        "context": [f"context for {input_text}"],
        "additional_metadata": {
            "context_quality": ctx_q,
            "synthetic_input_quality": input_q,
        },
    }


def _write_goldens(tmp_path, goldens: list[dict]) -> str:
    path = tmp_path / "goldens.json"
    path.write_text(json.dumps(goldens), encoding="utf-8")
    return str(path)


def _make_pipeline(
    mocker: MockerFixture, tmp_path, goldens: list[dict], **kwargs
) -> tuple[EvalPipeline, MockType, MockType]:
    mk_retriever: MockType = mocker.Mock(spec=RetrievalService)
    mk_retriever.retrieve_documents.return_value = {
        "documents": [{"text": "retrieved chunk"}],
        "final_answer": "the answer",
    }

    fake_result = mocker.MagicMock()
    fake_result.test_results = []
    mk_evaluator: MockType = mocker.Mock(spec=EvaluationPipeline)
    mk_evaluator.evaluate.return_value = fake_result

    pipeline = EvalPipeline(
        retriever_service=mk_retriever,
        evaluator=mk_evaluator,
        goldens_path=_write_goldens(tmp_path, goldens),
        report_path=str(tmp_path / "report.md"),
        **kwargs,
    )
    return pipeline, mk_retriever, mk_evaluator


class TestEvalPipeline:
    def test_filters_goldens_below_quality_threshold(
        self, mocker: MockerFixture, tmp_path
    ):
        goldens = [
            _golden("q1", 0.9, 0.9),  # passes
            _golden("q2", 0.9, 0.9),  # passes
            _golden("q3", 0.5, 0.9),  # fails: low context quality
        ]
        pipeline, mk_retriever, mk_evaluator = _make_pipeline(
            mocker, tmp_path, goldens, quality_threshold=0.8
        )

        report = pipeline.run()

        assert report.total_goldens == 3
        assert report.evaluated_count == 2
        assert mk_retriever.retrieve_documents.call_count == 2
        assert len(mk_evaluator.evaluate.call_args.args[0]) == 2

    def test_limit_caps_number_of_evaluated_goldens(
        self, mocker: MockerFixture, tmp_path
    ):
        goldens = [_golden(f"q{i}", 0.9, 0.9) for i in range(5)]
        pipeline, mk_retriever, _ = _make_pipeline(
            mocker, tmp_path, goldens, quality_threshold=0.8
        )

        report = pipeline.run(limit=2)

        assert report.evaluated_count == 2
        assert mk_retriever.retrieve_documents.call_count == 2

    def test_builds_test_case_from_golden_and_retrieval(
        self, mocker: MockerFixture, tmp_path
    ):
        goldens = [_golden("q1", 0.9, 0.9)]
        pipeline, _, mk_evaluator = _make_pipeline(
            mocker, tmp_path, goldens, quality_threshold=0.8
        )

        pipeline.run()

        test_case = mk_evaluator.evaluate.call_args.args[0][0]
        assert test_case.input == "q1"
        assert test_case.actual_output == "the answer"
        assert test_case.expected_output == "expected for q1"
        assert test_case.retrieval_context == ["retrieved chunk"]

    def test_writes_report_file(self, mocker: MockerFixture, tmp_path):
        goldens = [_golden("q1", 0.9, 0.9)]
        report_path = tmp_path / "out" / "report.md"
        mk_retriever: MockType = mocker.Mock(spec=RetrievalService)
        mk_retriever.retrieve_documents.return_value = {
            "documents": [{"text": "c"}],
            "final_answer": "a",
        }
        fake_result = mocker.MagicMock()
        fake_result.test_results = []
        mk_evaluator: MockType = mocker.Mock(spec=EvaluationPipeline)
        mk_evaluator.evaluate.return_value = fake_result

        pipeline = EvalPipeline(
            retriever_service=mk_retriever,
            evaluator=mk_evaluator,
            goldens_path=_write_goldens(tmp_path, goldens),
            report_path=str(report_path),
            quality_threshold=0.8,
        )

        result = pipeline.run()

        assert report_path.exists()
        assert result.report_path == str(report_path)
