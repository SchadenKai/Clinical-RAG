"""
Comprehensive unit tests for app.rag.chunker (ChunkerFactory & ChunkerService).
"""

from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture, MockType

from app.core.config import Settings
from app.rag.chunker import ChunkerFactory, ChunkerService
from app.services.llm.tokenizer import TokenizerService

# =============================================================================
# ChunkerFactory
# =============================================================================


class TestChunkerFactoryInit:
    """Tests for ChunkerFactory.__init__ default storage."""

    def test_defaults(self):
        factory = ChunkerFactory()
        assert factory.chunk_size == 1000
        assert factory.chunk_overlap == 200
        assert factory.tokenizer is None

    def test_custom_values(self):
        tok = MagicMock()
        factory = ChunkerFactory(tokenizer=tok, chunk_size=512, chunk_overlap=50)
        assert factory.chunk_size == 512
        assert factory.chunk_overlap == 50
        assert factory.tokenizer is tok


class TestChunkerFactoryGetSemantic:
    """Tests for get_semantic."""

    @patch("app.rag.chunker.SpacyTextSplitter", autospec=True)
    def test_uses_factory_defaults(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=800, chunk_overlap=100)
        factory.get_semantic()
        mock_cls.assert_called_once_with(
            pipeline="en_core_web_sm",
            chunk_size=800,
            chunk_overlap=100,
        )

    @patch("app.rag.chunker.SpacyTextSplitter", autospec=True)
    def test_explicit_overrides(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=800, chunk_overlap=100)
        factory.get_semantic(
            pipeline="en_core_web_lg", chunk_size=256, chunk_overlap=32
        )
        mock_cls.assert_called_once_with(
            pipeline="en_core_web_lg",
            chunk_size=256,
            chunk_overlap=32,
        )

    @patch("app.rag.chunker.SpacyTextSplitter", autospec=True)
    def test_partial_override_chunk_size_only(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=800, chunk_overlap=100)
        factory.get_semantic(chunk_size=300)
        mock_cls.assert_called_once_with(
            pipeline="en_core_web_sm",
            chunk_size=300,
            chunk_overlap=100,
        )

    @patch("app.rag.chunker.SpacyTextSplitter", autospec=True)
    def test_return_type(self, mock_cls: MockType):
        factory = ChunkerFactory()
        result = factory.get_semantic()
        assert result is mock_cls.return_value

    @patch("app.rag.chunker.SpacyTextSplitter", autospec=True)
    def test_extra_kwargs_forwarded(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_semantic(strip_whitespace=True)
        mock_cls.assert_called_once_with(
            pipeline="en_core_web_sm",
            chunk_size=1000,
            chunk_overlap=200,
            strip_whitespace=True,
        )


class TestChunkerFactoryGetRecursive:
    """Tests for get_recursive."""

    @patch("app.rag.chunker.RecursiveCharacterTextSplitter", autospec=True)
    def test_uses_factory_defaults(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=512, chunk_overlap=50)
        factory.get_recursive()
        mock_cls.assert_called_once_with(chunk_size=512, chunk_overlap=50)

    @patch("app.rag.chunker.RecursiveCharacterTextSplitter", autospec=True)
    def test_explicit_overrides(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=512, chunk_overlap=50)
        factory.get_recursive(chunk_size=128, chunk_overlap=10)
        mock_cls.assert_called_once_with(chunk_size=128, chunk_overlap=10)

    @patch("app.rag.chunker.RecursiveCharacterTextSplitter", autospec=True)
    def test_extra_kwargs(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_recursive(separators=["\n\n", "\n"])
        mock_cls.assert_called_once_with(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n"],
        )


class TestChunkerFactoryGetCharacterBased:
    """Tests for get_character_based."""

    @patch("app.rag.chunker.CharacterTextSplitter", autospec=True)
    def test_uses_factory_defaults(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=512, chunk_overlap=50)
        factory.get_character_based()
        mock_cls.assert_called_once_with(chunk_size=512, chunk_overlap=50)

    @patch("app.rag.chunker.CharacterTextSplitter", autospec=True)
    def test_explicit_overrides(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_character_based(chunk_size=256, chunk_overlap=20)
        mock_cls.assert_called_once_with(chunk_size=256, chunk_overlap=20)


class TestChunkerFactoryGetMarkdown:
    """Tests for get_markdown."""

    @patch("app.rag.chunker.MarkdownTextSplitter", autospec=True)
    def test_uses_factory_defaults(self, mock_cls: MockType):
        factory = ChunkerFactory(chunk_size=1024, chunk_overlap=128)
        factory.get_markdown()
        mock_cls.assert_called_once_with(chunk_size=1024, chunk_overlap=128)

    @patch("app.rag.chunker.MarkdownTextSplitter", autospec=True)
    def test_explicit_overrides(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_markdown(chunk_size=400, chunk_overlap=40)
        mock_cls.assert_called_once_with(chunk_size=400, chunk_overlap=40)

    @patch("app.rag.chunker.MarkdownTextSplitter", autospec=True)
    def test_extra_kwargs(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_markdown(strip_whitespace=False)
        mock_cls.assert_called_once_with(
            chunk_size=1000,
            chunk_overlap=200,
            strip_whitespace=False,
        )


class TestChunkerFactoryGetHybridHierarchal:
    """Tests for get_hybrid_hierarchal."""

    @patch("app.rag.chunker.HybridChunker", autospec=True)
    def test_uses_factory_tokenizer(self, mock_cls: MockType):
        tok = MagicMock()
        factory = ChunkerFactory(tokenizer=tok)
        factory.get_hybrid_hierarchal()
        mock_cls.assert_called_once_with(tokenizer=tok)

    @patch("app.rag.chunker.HybridChunker", autospec=True)
    def test_explicit_tokenizer_override(self, mock_cls: MockType):
        factory_tok = MagicMock()
        override_tok = MagicMock()
        factory = ChunkerFactory(tokenizer=factory_tok)
        factory.get_hybrid_hierarchal(tokenizer=override_tok)
        mock_cls.assert_called_once_with(tokenizer=override_tok)

    @patch("app.rag.chunker.HybridChunker", autospec=True)
    def test_none_tokenizer_when_factory_has_none(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_hybrid_hierarchal()
        mock_cls.assert_called_once_with(tokenizer=None)

    @patch("app.rag.chunker.HybridChunker", autospec=True)
    def test_extra_kwargs(self, mock_cls: MockType):
        factory = ChunkerFactory()
        factory.get_hybrid_hierarchal(merge_peers=True)
        mock_cls.assert_called_once_with(tokenizer=None, merge_peers=True)


# =============================================================================
# ChunkerService
# =============================================================================


class TestChunkerServiceInit:
    """Tests for ChunkerService.__init__."""

    @patch("app.rag.chunker.get_chunk_settings")
    def test_creates_factory_from_settings(
        self, mock_get_chunk: MockType, mocker: MockerFixture
    ):
        mock_get_chunk.return_value = {"chunk_size": 512, "chunk_overlap": 50}
        mock_tokenizer_svc = mocker.Mock(spec=TokenizerService)
        mock_tokenizer_svc.embedding_tokenizer = MagicMock(name="tok")
        mock_settings = mocker.Mock(spec=Settings)

        svc = ChunkerService(
            embedding_model="text-embedding-3-small",
            app_settings=mock_settings,
            tokenizer_service=mock_tokenizer_svc,
        )

        mock_get_chunk.assert_called_once_with(model_name="text-embedding-3-small")
        assert isinstance(svc.factory, ChunkerFactory)
        assert svc.factory.chunk_size == 512
        assert svc.factory.chunk_overlap == 50
        assert svc.factory.tokenizer is mock_tokenizer_svc.embedding_tokenizer

    @patch("app.rag.chunker.get_chunk_settings")
    def test_uses_injected_factory(
        self, mock_get_chunk: MockType, mocker: MockerFixture
    ):
        """When a factory is explicitly provided, it should be used as-is."""
        mock_get_chunk.return_value = {"chunk_size": 512, "chunk_overlap": 50}
        mock_tokenizer_svc = mocker.Mock(spec=TokenizerService)
        mock_tokenizer_svc.embedding_tokenizer = MagicMock()
        mock_settings = mocker.Mock(spec=Settings)
        custom_factory = ChunkerFactory(chunk_size=999, chunk_overlap=99)

        svc = ChunkerService(
            embedding_model="text-embedding-3-small",
            app_settings=mock_settings,
            tokenizer_service=mock_tokenizer_svc,
            chunker_factory=custom_factory,
        )

        assert svc.factory is custom_factory
        assert svc.factory.chunk_size == 999


class TestChunkerServiceGet:
    """Tests for ChunkerService.get dispatch and fallback logic."""

    @pytest.fixture
    def service(self, mocker: MockerFixture) -> ChunkerService:
        """Build a ChunkerService with a fully mocked factory."""
        with patch("app.rag.chunker.get_chunk_settings") as mock_gc:
            mock_gc.return_value = {"chunk_size": 512, "chunk_overlap": 50}
            mock_tokenizer_svc = mocker.Mock(spec=TokenizerService)
            mock_tokenizer_svc.embedding_tokenizer = MagicMock()
            mock_settings = mocker.Mock(spec=Settings)
            mock_settings.chunk_strategy = "recursive"

            svc = ChunkerService(
                embedding_model="text-embedding-3-small",
                app_settings=mock_settings,
                tokenizer_service=mock_tokenizer_svc,
            )
        # Replace the real factory with a mock so we can inspect calls
        svc.factory = mocker.Mock(spec=ChunkerFactory)
        return svc

    def test_dispatch_semantic(self, service: ChunkerService):
        result = service.get("semantic")
        service.factory.get_semantic.assert_called_once_with()
        assert result is service.factory.get_semantic.return_value

    def test_dispatch_recursive(self, service: ChunkerService):
        result = service.get("recursive")
        service.factory.get_recursive.assert_called_once_with()
        assert result is service.factory.get_recursive.return_value

    def test_dispatch_character_based(self, service: ChunkerService):
        result = service.get("character_based")
        service.factory.get_character_based.assert_called_once_with()
        assert result is service.factory.get_character_based.return_value

    def test_dispatch_markdown(self, service: ChunkerService):
        result = service.get("markdown")
        service.factory.get_markdown.assert_called_once_with()
        assert result is service.factory.get_markdown.return_value

    def test_dispatch_hybrid_hierarchal(self, service: ChunkerService):
        result = service.get("hybrid_hierarchal")
        service.factory.get_hybrid_hierarchal.assert_called_once_with()
        assert result is service.factory.get_hybrid_hierarchal.return_value

    def test_kwargs_forwarded(self, service: ChunkerService):
        service.get("recursive", chunk_size=256, chunk_overlap=10)
        service.factory.get_recursive.assert_called_once_with(
            chunk_size=256, chunk_overlap=10
        )

    def test_unsupported_chunker_falls_back(self, service: ChunkerService):
        result = service.get("nonexistent_chunker")
        service.factory.get_hybrid_hierarchal.assert_called_once_with()
        assert result is service.factory.get_hybrid_hierarchal.return_value

    def test_exception_falls_back_to_hybrid(self, service: ChunkerService):
        service.factory.get_recursive.side_effect = ValueError("boom")
        result = service.get("recursive")
        service.factory.get_hybrid_hierarchal.assert_called_once_with()
        assert result is service.factory.get_hybrid_hierarchal.return_value


class TestChunkerServiceChunkerProperty:
    """Tests for ChunkerService.chunker property."""

    @pytest.fixture
    def service(self, mocker: MockerFixture) -> ChunkerService:
        with patch("app.rag.chunker.get_chunk_settings") as mock_gc:
            mock_gc.return_value = {"chunk_size": 512, "chunk_overlap": 50}
            mock_tokenizer_svc = mocker.Mock(spec=TokenizerService)
            mock_tokenizer_svc.embedding_tokenizer = MagicMock()
            mock_settings = mocker.Mock(spec=Settings)
            mock_settings.chunk_strategy = "markdown"

            svc = ChunkerService(
                embedding_model="text-embedding-3-small",
                app_settings=mock_settings,
                tokenizer_service=mock_tokenizer_svc,
            )
        svc.factory = mocker.Mock(spec=ChunkerFactory)
        return svc

    def test_delegates_to_get_with_strategy(self, service: ChunkerService):
        result = service.chunker
        service.factory.get_markdown.assert_called_once_with()
        assert result is service.factory.get_markdown.return_value

    def test_falls_back_to_hybrid_when_no_settings(
        self, mocker: MockerFixture
    ):
        with patch("app.rag.chunker.get_chunk_settings") as mock_gc:
            mock_gc.return_value = {"chunk_size": 512, "chunk_overlap": 50}
            mock_tokenizer_svc = mocker.Mock(spec=TokenizerService)
            mock_tokenizer_svc.embedding_tokenizer = MagicMock()

            svc = ChunkerService(
                embedding_model="text-embedding-3-small",
                app_settings=None,
                tokenizer_service=mock_tokenizer_svc,
            )
        svc.factory = mocker.Mock(spec=ChunkerFactory)
        result = svc.chunker
        svc.factory.get_hybrid_hierarchal.assert_called_once_with()
        assert result is svc.factory.get_hybrid_hierarchal.return_value
