from deepeval.dataset.golden import Golden
from deepeval.models import DeepEvalBaseModel, GPTModel
from deepeval.models.base_model import DeepEvalBaseEmbeddingModel
from deepeval.models.embedding_models import LocalEmbeddingModel
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import ContextConstructionConfig

from app.core.config import Settings
from app.services.file_store.context_manager import FileProcessor
from app.services.file_store.db import S3Service


class SyntheticDataGenerator:
    def __init__(self, settings: Settings, s3_service: S3Service):
        self.settings: Settings = settings
        self._synthesizer: Synthesizer | None = None
        self._deepeval_model: DeepEvalBaseModel | None = None
        self.s3_service: S3Service = s3_service
        self._embedder: DeepEvalBaseEmbeddingModel | None = None

    @property
    def deepeval_model(self) -> DeepEvalBaseModel:
        if self._deepeval_model:
            return self._deepeval_model
        self._deepeval_model = GPTModel(
            model=self.settings.llm_model_name,
            api_key=self.settings.llm_api_key,
            base_url="https://api.studio.nebius.ai/v1/",
        )
        return self._deepeval_model

    @property
    def embedder(self) -> DeepEvalBaseEmbeddingModel:
        if self._embedder:
            return self._embedder
        self._embedder = LocalEmbeddingModel(
            model=self.settings.bi_encoder_model,
            api_key=self.settings.embedding_api_key,
            base_url="https://api.studio.nebius.ai/v1/",
        )
        return self._embedder

    @property
    def synthesizer(self) -> Synthesizer:
        if self._synthesizer:
            return self._synthesizer
        self._synthesizer = Synthesizer(
            model=self.deepeval_model, cost_tracking=True, async_mode=False
        )
        return self._synthesizer

    def generate(self) -> list[Golden]:
        test_dataset = []
        s3_client = self.s3_service.client
        objects = s3_client.list_objects(Bucket=self.settings.minio_bucket_name)
        file_keys = (
            [obj["Key"] for obj in objects["Contents"]]
            if objects.get("Contents")
            else []
        )
        if file_keys == []:
            return file_keys

        for file_key in file_keys:
            with FileProcessor(
                s3_service=self.s3_service, file_key=file_key, settings=self.settings
            ) as file_path:
                results = self.synthesizer.generate_goldens_from_docs(
                    document_paths=[file_path.as_posix()],
                    context_construction_config=ContextConstructionConfig(
                        embedder=self.embedder,
                        context_quality_threshold=0.0,
                        critic_model=self.deepeval_model,
                    ),
                    include_expected_output=True,
                )
                test_dataset.append(results)

        return test_dataset
