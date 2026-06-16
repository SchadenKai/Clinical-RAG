from deepeval.dataset.golden import Golden
from deepeval.models import DeepEvalBaseModel, GPTModel
from deepeval.models.base_model import DeepEvalBaseEmbeddingModel
from deepeval.models.embedding_models import LocalEmbeddingModel
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import ContextConstructionConfig

from app.core.config import Settings
from app.logger import app_logger
from app.services.file_store.context_manager import S3FileStager
from app.services.file_store.db import S3Service
from app.services.llm.calculate_cost import get_pricing_info

# Nebius AI hosts the judge/critic and embedding models behind an
# OpenAI-compatible API, which deepeval's GPTModel/LocalEmbeddingModel target.
NEBIUS_BASE_URL = "https://api.studio.nebius.ai/v1/"

# deepeval scores each context's quality during generation. We keep every
# context (threshold 0.0) and let the evaluation pipeline apply the quality bar
# downstream, so the golden artifact stays broad and the eval step owns
# filtering. See app.pipelines.evaluation.DEFAULT_QUALITY_THRESHOLD.
CONTEXT_QUALITY_THRESHOLD = 0.0


class SyntheticDataGenerator:
    """deepeval-backed synthetic golden generator.

    Generates evaluation goldens from source documents in the object store.
    This class is generation-only; persisting goldens as a reusable artifact is
    the responsibility of ``app.pipelines.sdg.SdgPipeline``.
    """

    def __init__(self, settings: Settings, s3_service: S3Service):
        self.settings: Settings = settings
        self.s3_service: S3Service = s3_service
        self._synthesizer: Synthesizer | None = None
        self._deepeval_model: DeepEvalBaseModel | None = None
        self._embedder: DeepEvalBaseEmbeddingModel | None = None

    @property
    def deepeval_model(self) -> DeepEvalBaseModel:
        """Judge/critic model.

        Since we use Nebius AI models through deepeval's GPTModel API, the cost
        values must be set explicitly so deepeval does not introduce silent
        cost-tracking errors.
        """
        if self._deepeval_model:
            return self._deepeval_model
        output_price, input_price = get_pricing_info(self.settings.llm_model_name)
        self._deepeval_model = GPTModel(
            model=self.settings.llm_model_name,
            api_key=self.settings.llm_api_key,
            base_url=NEBIUS_BASE_URL,
            cost_per_input_token=input_price,
            cost_per_output_token=output_price,
        )
        return self._deepeval_model

    @property
    def embedder(self) -> DeepEvalBaseEmbeddingModel:
        if self._embedder:
            return self._embedder
        self._embedder = LocalEmbeddingModel(
            model=self.settings.embedding_model,
            api_key=self.settings.embedding_api_key,
            base_url=NEBIUS_BASE_URL,
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

    def _list_source_keys(self) -> list[str]:
        # Paginate: list_objects (v1) silently caps at 1000 keys.
        s3_client = self.s3_service.client
        paginator = s3_client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self.settings.minio_bucket_name):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return keys

    def generate(
        self,
        file_keys: list[str] | None = None,
        max_goldens_per_context: int = 10,
        max_contexts_per_document: int = 50,
    ) -> list[Golden]:
        """Generate goldens for the given documents.

        Args:
            file_keys: Object-store keys to generate from. When ``None`` every
                object in the configured bucket is used.
            max_goldens_per_context: Upper bound on goldens per context window.
            max_contexts_per_document: Upper bound on contexts per document.

        Returns:
            A flat list of generated goldens (empty when there are no sources).
        """
        keys = file_keys if file_keys is not None else self._list_source_keys()
        if not keys:
            app_logger.warning("SDG: no source documents found; nothing to generate")
            return []

        goldens: list[Golden] = []
        try:
            for file_key in keys:
                app_logger.info("SDG: generating goldens from %s", file_key)
                with S3FileStager(
                    s3_service=self.s3_service,
                    file_key=file_key,
                    settings=self.settings,
                ) as file_path:
                    results = self.synthesizer.generate_goldens_from_docs(
                        document_paths=[file_path.as_posix()],
                        context_construction_config=ContextConstructionConfig(
                            embedder=self.embedder,
                            context_quality_threshold=CONTEXT_QUALITY_THRESHOLD,
                            critic_model=self.deepeval_model,
                            max_contexts_per_document=max_contexts_per_document,
                            chunk_overlap=self.settings.chunk_overlap,
                            chunk_size=self.settings.chunk_size,
                        ),
                        max_goldens_per_context=max_goldens_per_context,
                        include_expected_output=True,
                    )
                    goldens.extend(results)
        except Exception as e:
            raise RuntimeError(f"Something went wrong during generation: {e}") from e

        app_logger.info(
            "SDG: generated %d golden(s) from %d document(s)", len(goldens), len(keys)
        )
        return goldens
