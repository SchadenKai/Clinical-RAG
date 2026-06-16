import json

from pytest_mock import MockerFixture, MockType

from app.pipelines.sdg import SdgPipeline
from app.services.sdg import SyntheticDataGenerator


class _FakeGolden:
    """Golden-like object exposing model_dump, mirroring deepeval Goldens."""

    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self, mode: str = "python") -> dict:
        return self._payload


class TestSdgPipeline:
    def test_run_persists_serialized_goldens(self, mocker: MockerFixture, tmp_path):
        goldens = [
            _FakeGolden({"input": "q1", "expected_output": "a1"}),
            _FakeGolden({"input": "q2", "expected_output": "a2"}),
        ]
        mk_generator: MockType = mocker.Mock(spec=SyntheticDataGenerator)
        mk_generator.generate.return_value = goldens

        output_path = tmp_path / "goldens.json"
        pipeline = SdgPipeline(generator=mk_generator, output_path=str(output_path))

        report = pipeline.run(file_keys=["a.pdf"], max_goldens_per_context=3)

        mk_generator.generate.assert_called_once_with(
            file_keys=["a.pdf"], max_goldens_per_context=3
        )
        assert report.golden_count == 2
        assert report.output_path == str(output_path)

        written = json.loads(output_path.read_text(encoding="utf-8"))
        assert written == [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]

    def test_run_serializes_goldens_without_model_dump(
        self, mocker: MockerFixture, tmp_path
    ):
        # Golden-like object lacking model_dump exercises the attribute fallback.
        golden = mocker.Mock(spec=["input", "expected_output", "context"])
        golden.input = "q"
        golden.expected_output = "a"
        golden.context = ["c"]
        mk_generator: MockType = mocker.Mock(spec=SyntheticDataGenerator)
        mk_generator.generate.return_value = [golden]

        output_path = tmp_path / "goldens.json"
        pipeline = SdgPipeline(generator=mk_generator, output_path=str(output_path))

        pipeline.run()

        written = json.loads(output_path.read_text(encoding="utf-8"))
        assert written == [
            {
                "input": "q",
                "expected_output": "a",
                "context": ["c"],
                "additional_metadata": None,
            }
        ]

    def test_run_with_no_goldens_writes_empty_list(
        self, mocker: MockerFixture, tmp_path
    ):
        mk_generator: MockType = mocker.Mock(spec=SyntheticDataGenerator)
        mk_generator.generate.return_value = []

        output_path = tmp_path / "nested" / "goldens.json"
        pipeline = SdgPipeline(generator=mk_generator, output_path=str(output_path))

        report = pipeline.run()

        assert report.golden_count == 0
        # Parent directory is created on demand.
        assert json.loads(output_path.read_text(encoding="utf-8")) == []
