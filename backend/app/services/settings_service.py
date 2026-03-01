from sqlalchemy.orm import Session

from app.db.models import Document, EmbeddingConfig, LLMConfig
from app.logger import app_logger


class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_llm_config(self) -> LLMConfig:
        return self.db.query(LLMConfig).filter(LLMConfig.is_active).first()

    def update_llm_config(
        self, provider: str, model_name: str, api_key: str
    ) -> LLMConfig:
        current = self.get_active_llm_config()
        if current:
            current.is_active = False

        new_config = LLMConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            is_active=True,
        )
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        return new_config

    def get_active_embedding_config(self) -> EmbeddingConfig:
        return self.db.query(EmbeddingConfig).filter(EmbeddingConfig.is_active).first()

    def update_embedding_config(
        self, provider: str, model_name: str, api_key: str
    ) -> dict:
        """
        Updates embedding config. Marks all Documents as PENDING since the
        embedding model changed, making all existing vectors invalid.
        """
        current = self.get_active_embedding_config()
        if current:
            current.is_active = False

        new_config = EmbeddingConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            is_active=True,
        )
        self.db.add(new_config)

        # Mark all documents as PENDING for re-indexing
        updated_count = (
            self.db.query(Document)
            .filter(Document.status != "PENDING")
            .update({"status": "PENDING"})
        )

        self.db.commit()
        self.db.refresh(new_config)

        app_logger.warning(
            f"Embedding config updated. "
            f"{updated_count} documents marked for re-indexing."
        )

        return {
            "config": new_config,
            "documents_affected": updated_count,
            "message": (
                "Warning: Embedding model changed. "
                "Vector database must be cleared and documents must be re-indexed."
            ),
        }
