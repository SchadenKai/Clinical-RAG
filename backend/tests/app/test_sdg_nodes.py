from docling_core.types.doc.document import DoclingDocument
from pytest_mock import MockerFixture, MockType

from app.agent.sdg.context import AgentContext
from app.agent.sdg.models import SdgProgressEnum
from app.agent.sdg.nodes import (
    document_preparation_node,
    file_ingestion_node,
    knowledge_graph_node,
    store_goldens_node,
    testset_generation_node,
)
from app.agent.sdg.state import AgentState
from app.core.config import Settings


def _make_runtime(mocker: MockerFixture):
    mk_settings: MockType = mocker.Mock(spec=Settings)
    mk_settings.minio_bucket_name = "test-bucket"
    mk_settings.pdf_batch_size = 4

    mk_s3_client: MockType = mocker.MagicMock()
    mk_s3_service: MockType = mocker.MagicMock()
    mk_s3_service.client = mk_s3_client

    mk_context: MockType = mocker.Mock(spec=AgentContext)
    mk_context.settings = mk_settings
    mk_context.s3_service = mk_s3_service
    mk_context.llm_service = mocker.MagicMock()
    mk_context.embedding_service = mocker.MagicMock()

    runtime = mocker.MagicMock()
    runtime.context = mk_context
    return runtime, mk_s3_client


class TestFileIngestionNode:
    def test_returns_raw_document_and_loading_status(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        mocker.patch("app.agent.sdg.nodes.doc_converter", return_value=fake_doc)

        fake_path = "/tmp/fake_file.pdf"
        mock_stager = mocker.MagicMock()
        mock_stager.__enter__ = mocker.Mock(return_value=fake_path)
        mock_stager.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("app.agent.sdg.nodes.S3FileStager", return_value=mock_stager)

        state = AgentState(file_key="uploads/test.pdf")
        result = file_ingestion_node(state, runtime)

        assert result["raw_document"] is fake_doc
        assert result["progress_status"] == SdgProgressEnum.LOADING_FILE


class TestDocumentPreparationNode:
    def test_multi_page_doc_produces_one_document_per_page(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        fake_doc.pages = {1: mocker.Mock(), 2: mocker.Mock(), 3: mocker.Mock()}
        fake_doc.export_to_markdown.side_effect = lambda page_range=None: (
            f"page {page_range[0]} content" if page_range else "full content"
        )

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf", raw_document=fake_doc
        )
        result = document_preparation_node(state, runtime)

        docs = result["langchain_documents"]
        assert len(docs) == 3
        assert all(d.metadata["source"] == "uploads/doc.pdf" for d in docs)
        assert all("page" in d.metadata for d in docs)
        assert result["progress_status"] == SdgProgressEnum.PREPARING_DOCUMENTS

    def test_empty_pages_in_multipage_doc_are_skipped(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        fake_doc.pages = {1: mocker.Mock(), 2: mocker.Mock()}

        def _export(page_range=None):
            if page_range == (1, 1):
                return "page 1 content"
            if page_range == (2, 2):
                return "   "  # blank page
            return "full content"

        fake_doc.export_to_markdown.side_effect = _export

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf", raw_document=fake_doc
        )
        result = document_preparation_node(state, runtime)

        docs = result["langchain_documents"]
        assert len(docs) == 1
        assert docs[0].page_content == "page 1 content"

    def test_single_page_doc_produces_one_document_with_no_page_metadata(
        self, mocker: MockerFixture
    ):
        runtime, _ = _make_runtime(mocker)

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        fake_doc.pages = {1: mocker.Mock()}
        fake_doc.export_to_markdown.return_value = "single page content"

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf", raw_document=fake_doc
        )
        result = document_preparation_node(state, runtime)

        docs = result["langchain_documents"]
        assert len(docs) == 1
        assert "page" not in docs[0].metadata
        assert docs[0].metadata["source"] == "uploads/doc.pdf"

    def test_no_pages_dict_falls_back_to_full_export(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_doc: MockType = mocker.Mock(spec=DoclingDocument)
        fake_doc.pages = {}
        fake_doc.export_to_markdown.return_value = "full document text"

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf", raw_document=fake_doc
        )
        result = document_preparation_node(state, runtime)

        docs = result["langchain_documents"]
        assert len(docs) == 1
        assert docs[0].page_content == "full document text"


class TestKnowledgeGraphNode:
    def test_builds_knowledge_graph(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)
        mocker.patch("app.agent.sdg.nodes.apply_transforms")
        mocker.patch("app.agent.sdg.nodes.default_transforms", return_value=[])

        from langchain_core.documents import Document

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf",
            testset_size=5,
            langchain_documents=[
                Document(page_content="some text", metadata={"source": "doc.pdf"})
            ],
        )
        result = knowledge_graph_node(state, runtime)

        assert result["knowledge_graph"] is not None
        assert result.get("error") is None
        assert result["progress_status"] == SdgProgressEnum.BUILDING_KNOWLEDGE_GRAPH

    def test_value_error_sets_error_field(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)
        mocker.patch(
            "app.agent.sdg.nodes.apply_transforms",
            side_effect=ValueError("document too short"),
        )
        mocker.patch("app.agent.sdg.nodes.default_transforms", return_value=[])

        from langchain_core.documents import Document

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf",
            testset_size=5,
            langchain_documents=[Document(page_content="x", metadata={})],
        )
        result = knowledge_graph_node(state, runtime)

        assert result["error"] == "document too short"
        assert result["knowledge_graph"] is not None
        assert result["progress_status"] == SdgProgressEnum.BUILDING_KNOWLEDGE_GRAPH

    def test_unexpected_exception_sets_error_field(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)
        mocker.patch(
            "app.agent.sdg.nodes.apply_transforms",
            side_effect=RuntimeError("network error"),
        )
        mocker.patch("app.agent.sdg.nodes.default_transforms", return_value=[])

        from langchain_core.documents import Document

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf",
            testset_size=5,
            langchain_documents=[Document(page_content="text", metadata={})],
        )
        result = knowledge_graph_node(state, runtime)

        assert result["error"] == "network error"
        assert result["progress_status"] == SdgProgressEnum.BUILDING_KNOWLEDGE_GRAPH


class TestTestsetGenerationNode:
    def test_generates_goldens_on_success(self, mocker: MockerFixture):
        runtime, _ = _make_runtime(mocker)

        fake_goldens = [{"user_input": "q1", "reference": "a1"}]
        mock_testset = mocker.MagicMock()
        mock_testset.to_list.return_value = fake_goldens

        mock_generator = mocker.MagicMock()
        mock_generator.generate.return_value = mock_testset

        mocker.patch(
            "app.agent.sdg.nodes.TestsetGenerator", return_value=mock_generator
        )

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf",
            testset_size=1,
            knowledge_graph=mocker.MagicMock(),
        )
        result = testset_generation_node(state, runtime)

        assert result["goldens"] == fake_goldens
        assert result.get("error") is None
        assert result["progress_status"] == SdgProgressEnum.GENERATING_TESTSET

    def test_exception_sets_error_field_and_returns_empty_goldens(
        self, mocker: MockerFixture
    ):
        runtime, _ = _make_runtime(mocker)

        mock_generator = mocker.MagicMock()
        mock_generator.generate.side_effect = RuntimeError("generation failed")

        mocker.patch(
            "app.agent.sdg.nodes.TestsetGenerator", return_value=mock_generator
        )

        state = AgentState.model_construct(
            file_key="uploads/doc.pdf",
            testset_size=5,
            knowledge_graph=mocker.MagicMock(),
        )
        result = testset_generation_node(state, runtime)

        assert result["goldens"] == []
        assert result["error"] == "generation failed"
        assert result["progress_status"] == SdgProgressEnum.GENERATING_TESTSET


class TestStoreGoldensNode:
    def test_stores_goldens_to_s3_and_returns_output_path(self, mocker: MockerFixture):
        runtime, mk_s3_client = _make_runtime(mocker)

        goldens = [{"user_input": "q", "reference": "a"}]
        state = AgentState.model_construct(
            file_key="uploads/report.pdf", goldens=goldens
        )
        result = store_goldens_node(state, runtime)

        mk_s3_client.put_object.assert_called_once()
        call_kwargs = mk_s3_client.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"].startswith("goldens/report_")
        assert call_kwargs["Key"].endswith(".json")
        assert result["output_path"] == call_kwargs["Key"]
        assert result.get("error") is None
        assert result["progress_status"] == SdgProgressEnum.DONE

    def test_skips_s3_when_no_goldens(self, mocker: MockerFixture):
        runtime, mk_s3_client = _make_runtime(mocker)

        state = AgentState.model_construct(file_key="uploads/doc.pdf", goldens=[])
        result = store_goldens_node(state, runtime)

        mk_s3_client.put_object.assert_not_called()
        assert result["progress_status"] == SdgProgressEnum.DONE

    def test_s3_error_sets_error_field(self, mocker: MockerFixture):
        runtime, mk_s3_client = _make_runtime(mocker)
        mk_s3_client.put_object.side_effect = OSError("connection refused")

        goldens = [{"user_input": "q", "reference": "a"}]
        state = AgentState.model_construct(file_key="uploads/doc.pdf", goldens=goldens)
        result = store_goldens_node(state, runtime)

        assert result["error"] == "connection refused"
        assert result.get("output_path") is None
        assert result["progress_status"] == SdgProgressEnum.DONE

    def test_json_serialization_uses_default_str_for_non_primitives(
        self, mocker: MockerFixture
    ):
        runtime, mk_s3_client = _make_runtime(mocker)

        # Simulate a non-serializable type in goldens (e.g., a custom object)
        class _Unserializable:
            def __str__(self):
                return "serialized_value"

        goldens = [{"user_input": _Unserializable()}]
        state = AgentState.model_construct(file_key="uploads/doc.pdf", goldens=goldens)
        # Should not raise; default=str converts _Unserializable to its str repr
        result = store_goldens_node(state, runtime)

        mk_s3_client.put_object.assert_called_once()
        body: bytes = mk_s3_client.put_object.call_args.kwargs["Body"]
        assert b"serialized_value" in body
        assert result.get("error") is None
