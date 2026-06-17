from dagster import RunConfig, materialize
from pytest_mock import MockerFixture

from app.orchestration.assets import (
    EvalConfig,
    evaluation_report,
    golden_dataset,
    indexed_documents,
)

ASSETS = [indexed_documents, golden_dataset, evaluation_report]


def _stub_pipelines(mocker: MockerFixture):
    """Patch all three pipeline factories so materialization needs no services.

    Every asset emits scalar metadata, so each stubbed `run()` must return an
    object with the real numeric/string attributes the asset reads.
    """
    idx = mocker.Mock()
    idx.run.return_value = mocker.Mock(total=1, succeeded=1, failed=0)
    sdg = mocker.Mock()
    sdg.run.return_value = mocker.Mock(golden_count=3, output_path="g.json")
    ev = mocker.Mock()
    ev.run.return_value = mocker.Mock(
        evaluated_count=2, total_goldens=3, report_path="r.md"
    )

    mocker.patch(
        "app.orchestration.assets.IndexingPipeline.from_manual", return_value=idx
    )
    mocker.patch("app.orchestration.assets.SdgPipeline.from_manual", return_value=sdg)
    ev_from_manual = mocker.patch(
        "app.orchestration.assets.EvalPipeline.from_manual", return_value=ev
    )
    return idx, sdg, ev, ev_from_manual


class TestOrchestrationAssets:
    def test_assets_materialize_and_invoke_pipelines_in_order(
        self, mocker: MockerFixture
    ):
        idx, sdg, ev, _ = _stub_pipelines(mocker)

        result = materialize(ASSETS)

        # A successful in-process run proves the deps resolve and the upstream
        # assets ran before evaluation_report.
        assert result.success
        idx.run.assert_called_once()
        sdg.run.assert_called_once()
        ev.run.assert_called_once()

    def test_eval_asset_passes_config_through_to_pipeline(self, mocker: MockerFixture):
        _, _, ev, ev_from_manual = _stub_pipelines(mocker)

        result = materialize(
            ASSETS,
            run_config=RunConfig(
                ops={"evaluation_report": EvalConfig(quality_threshold=0.5, limit=4)}
            ),
        )

        assert result.success
        ev_from_manual.assert_called_once_with(quality_threshold=0.5)
        ev.run.assert_called_once_with(limit=4)
