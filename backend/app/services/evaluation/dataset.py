import json
import threading

from deepeval.dataset.golden import Golden
from deepeval.models import DeepEvalBaseModel, GPTModel
from deepeval.models.base_model import DeepEvalBaseEmbeddingModel
from deepeval.models.embedding_models import LocalEmbeddingModel
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import ContextConstructionConfig

from app.core.config import Settings
from app.services.file_store.context_manager import S3FileStager
from app.services.file_store.db import S3Service
from app.services.llm.calculate_cost import get_pricing_info


class SyntheticDataGenerator:
    def __init__(self, settings: Settings, s3_service: S3Service):
        self.settings: Settings = settings
        self._synthesizer: Synthesizer | None = None
        self._deepeval_model: DeepEvalBaseModel | None = None
        self.s3_service: S3Service = s3_service
        self._embedder: DeepEvalBaseEmbeddingModel | None = None

    @property
    def deepeval_model(self) -> DeepEvalBaseModel:
        """
        Since we are using Nebius AI models with GPIModel API
        it is important to specify the cost values so that
        it will not introduce silent errors in deepeval.
        """
        if self._deepeval_model:
            return self._deepeval_model
        output_price, input_price = get_pricing_info(self.settings.llm_model_name)
        self._deepeval_model = GPTModel(
            model=self.settings.llm_model_name,
            api_key=self.settings.llm_api_key,
            base_url="https://api.studio.nebius.ai/v1/",
            cost_per_input_token=input_price,
            cost_per_output_token=output_price,
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

    def _store_dataset_locally(self, results: list[list[Golden]]) -> None:
        file_path = "app/data/reports/synthetic_golden_dataset.json"
        flatten_goldens = [
            {
                "input": golden.input,
                "expected_output": golden.expected_output,
                "context": golden.context,
                "additional_metadata": golden.additional_metadata,
            }
            for golden_list in results
            for golden in golden_list
        ]
        with open(file=file_path, mode="w") as json_file:
            json.dump(flatten_goldens, json_file, indent=4)
        return None

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
        try:
            for file_key in file_keys:
                with S3FileStager(
                    s3_service=self.s3_service,
                    file_key=file_key,
                    settings=self.settings,
                ) as file_path:
                    results = self.synthesizer.generate_goldens_from_docs(
                        document_paths=[file_path.as_posix()],
                        context_construction_config=ContextConstructionConfig(
                            embedder=self.embedder,
                            context_quality_threshold=0.0,
                            critic_model=self.deepeval_model,
                            max_contexts_per_document=50,
                            chunk_overlap=self.settings.chunk_overlap,
                            chunk_size=self.settings.chunk_size,
                        ),
                        max_goldens_per_context=10,
                        include_expected_output=True,
                    )
                    test_dataset.append(results)
        except Exception as e:
            raise RuntimeError(f"Something went wrong during generation: {e}") from e
        threading.Thread(
            target=self._store_dataset_locally, args=(test_dataset,)
        ).start()
        return test_dataset
