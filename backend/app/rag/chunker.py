from typing import Any, Literal

from docling.chunking import HybridChunker
from langchain_text_splitters import (
    CharacterTextSplitter,
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    SpacyTextSplitter,
)

from app.core.config import Settings
from app.logger import app_logger
from app.rag.utils import get_chunk_settings
from app.services.llm.tokenizer import TokenizerService

_CHUNKERS_NAME = Literal[
    "semantic", "recursive", "character_based", "markdown", "hybrid_hierarchal"
]


class ChunkerFactory:
    """
    Factory for creating text splitter instances with consistent default parameters.

    Encapsulates default chunk_size, chunk_overlap, and tokenizer so that every
    splitter produced by this factory shares the same baseline configuration
    unless explicitly overridden at creation time.
    """

    def __init__(
        self,
        tokenizer: Any = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self.tokenizer = tokenizer
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # -- individual splitter creators ----------------------------------------

    def get_semantic(
        self,
        pipeline: str = "en_core_web_sm",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        **kwargs: Any,
    ) -> SpacyTextSplitter:
        return SpacyTextSplitter(
            pipeline=pipeline,
            chunk_size=chunk_size if chunk_size is not None else self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            **kwargs,
        )

    def get_recursive(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        **kwargs: Any,
    ) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size if chunk_size is not None else self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            **kwargs,
        )

    def get_character_based(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        **kwargs: Any,
    ) -> CharacterTextSplitter:
        return CharacterTextSplitter(
            chunk_size=chunk_size if chunk_size is not None else self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            **kwargs,
        )

    def get_markdown(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        **kwargs: Any,
    ) -> MarkdownTextSplitter:
        return MarkdownTextSplitter(
            chunk_size=chunk_size if chunk_size is not None else self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            **kwargs,
        )

    def get_hybrid_hierarchal(
        self,
        tokenizer: Any | None = None,
        **kwargs: Any,
    ) -> HybridChunker:
        return HybridChunker(
            tokenizer=tokenizer if tokenizer is not None else self.tokenizer,
            **kwargs,
        )


class ChunkerService:
    def __init__(
        self,
        embedding_model: str,
        app_settings: Settings,
        tokenizer_service: TokenizerService,
        chunker_factory: ChunkerFactory | None = None,
    ):
        self.embedding_model: str = embedding_model
        self.app_settings: Settings = app_settings
        self.tokenizer_service = tokenizer_service

        # Resolve default chunk parameters and tokenizer once at init
        chunk_info = get_chunk_settings(model_name=self.embedding_model)
        tokenizer = self.tokenizer_service.embedding_tokenizer

        self.factory = chunker_factory or ChunkerFactory(
            tokenizer=tokenizer,
            chunk_size=chunk_info["chunk_size"],
            chunk_overlap=chunk_info["chunk_overlap"],
        )

    def get(self, chunker_name: _CHUNKERS_NAME, **kwargs: Any) -> Any:
        _DISPATCH = {
            "semantic": self.factory.get_semantic,
            "recursive": self.factory.get_recursive,
            "character_based": self.factory.get_character_based,
            "markdown": self.factory.get_markdown,
            "hybrid_hierarchal": self.factory.get_hybrid_hierarchal,
        }

        try:
            creator = _DISPATCH.get(chunker_name)
            if creator is None:
                app_logger.warning(
                    f"Chunker '{chunker_name}' is not supported. "
                    "Falling back to default hybrid hierarchal chunker"
                )
                return self.factory.get_hybrid_hierarchal()
            return creator(**kwargs)
        except Exception as e:
            app_logger.error(
                f"Failed to initialize chunker {chunker_name} with params {kwargs}: {e}"
            )
            return self.factory.get_hybrid_hierarchal()

    @property
    def chunker(self) -> Any:
        strategy: Any = (
            self.app_settings.chunk_strategy
            if self.app_settings
            else "hybrid_hierarchal"
        )
        return self.get(strategy)
