from docling.chunking import HierarchicalChunker
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, tbale 

from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.settings import get_app_settings
from app.services.file_store.context_manager import S3FileStager

_FILE_NAME = "9789240115774-eng.pdf"

doc_converter = DocumentConverter()

app_settings = get_app_settings()
s3_service = get_s3_service(app_settings)

with S3FileStager(
    s3_service=s3_service, file_key=_FILE_NAME, settings=app_settings
) as file_path:
    pdf_pipeline_options = 
    doc = doc_converter.convert(file_path)
    doc = doc.document
    chunks = doc.texts
    new_chunks = []
    print(f"Initial number of chunks: {len(chunks)}")
    chunker = HierarchicalChunker(always_emit_headings=True, merge_list_items=True)
    chunks = chunker.chunk(doc)
    chunks = list(chunks)
    print(f"Number of chunks after hierachal chunking: {len(chunks)}")
