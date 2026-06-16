import pytest
from pytest_mock import MockerFixture, MockType

from app.core.config import Settings
from app.services.file_store.db import S3Service
from app.services.sdg import SyntheticDataGenerator


def _make_generator(mocker: MockerFixture) -> tuple[SyntheticDataGenerator, MockType]:
    mk_settings: MockType = mocker.Mock(spec=Settings)
    mk_settings.minio_bucket_name = "test-bucket"
    mk_settings.chunk_size = 512
    mk_settings.chunk_overlap = 64
    mk_settings.embedding_model = "text-embedding-3-small"
    mk_settings.llm_model_name = "gpt-4o"
    mk_settings.llm_api_key = "key"
    mk_settings.embedding_api_key = "key"

    mk_s3_client: MockType = mocker.MagicMock()
    mk_s3_service: MockType = mocker.Mock(spec=S3Service)
    mk_s3_service.client = mk_s3_client

    generator = SyntheticDataGenerator(settings=mk_settings, s3_service=mk_s3_service)
    return generator, mk_s3_client


class TestListSourceKeys:
    def test_returns_keys_across_paginated_pages(self, mocker: MockerFixture):
        generator, mk_s3_client = _make_generator(mocker)
        mk_paginator: MockType = mocker.MagicMock()
        mk_paginator.paginate.return_value = [
            {"Contents": [{"Key": "a.pdf"}]},
            {"Contents": [{"Key": "b.pdf"}]},
        ]
        mk_s3_client.get_paginator.return_value = mk_paginator

        assert generator._list_source_keys() == ["a.pdf", "b.pdf"]
        mk_s3_client.get_paginator.assert_called_once_with("list_objects_v2")

    def test_returns_empty_when_bucket_empty(self, mocker: MockerFixture):
        generator, mk_s3_client = _make_generator(mocker)
        mk_paginator: MockType = mocker.MagicMock()
        mk_paginator.paginate.return_value = [{}]
        mk_s3_client.get_paginator.return_value = mk_paginator

        assert generator._list_source_keys() == []


class TestGenerate:
    def test_returns_empty_when_no_sources(self, mocker: MockerFixture):
        generator, _ = _make_generator(mocker)
        # Explicit empty list short-circuits without touching the synthesizer.
        assert generator.generate(file_keys=[]) == []

    def test_generates_and_flattens_goldens(self, mocker: MockerFixture):
        generator, _ = _make_generator(mocker)

        # Short-circuit the lazily-built deepeval models/synthesizer.
        fake_synth: MockType = mocker.MagicMock()
        fake_synth.generate_goldens_from_docs.return_value = ["g1", "g2"]
        generator._synthesizer = fake_synth
        generator._embedder = mocker.MagicMock()
        generator._deepeval_model = mocker.MagicMock()

        mocker.patch("app.services.sdg.ContextConstructionConfig")
        fake_path = mocker.MagicMock()
        fake_path.as_posix.return_value = "/tmp/a.pdf"
        stager = mocker.MagicMock()
        stager.__enter__ = mocker.Mock(return_value=fake_path)
        stager.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("app.services.sdg.S3FileStager", return_value=stager)

        goldens = generator.generate(file_keys=["a.pdf"])

        assert goldens == ["g1", "g2"]
        fake_synth.generate_goldens_from_docs.assert_called_once()
        call_kwargs = fake_synth.generate_goldens_from_docs.call_args.kwargs
        assert call_kwargs["document_paths"] == ["/tmp/a.pdf"]

    def test_wraps_generation_errors_in_runtime_error(self, mocker: MockerFixture):
        generator, _ = _make_generator(mocker)
        fake_synth: MockType = mocker.MagicMock()
        fake_synth.generate_goldens_from_docs.side_effect = ValueError("bad doc")
        generator._synthesizer = fake_synth
        generator._embedder = mocker.MagicMock()
        generator._deepeval_model = mocker.MagicMock()

        mocker.patch("app.services.sdg.ContextConstructionConfig")
        stager = mocker.MagicMock()
        stager.__enter__ = mocker.Mock(return_value=mocker.MagicMock())
        stager.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("app.services.sdg.S3FileStager", return_value=stager)

        with pytest.raises(RuntimeError):
            generator.generate(file_keys=["a.pdf"])
