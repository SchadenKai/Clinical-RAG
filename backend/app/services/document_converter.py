from pathlib import Path

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    OcrAutoOptions,
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument


def doc_converter(path: Path, page_batch_size: int = 10) -> DoclingDocument:
    pdf_pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.AUTO),
        do_ocr=True,
        # Picture AI features disabled — vision models are the primary VRAM consumers
        # on long PDFs and offer minimal value for text-based clinical RAG retrieval.
        # Re-enable if figure understanding becomes a priority.
        generate_picture_images=False,
        do_picture_description=False,
        do_picture_classification=False,
        # table-related configurations
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            do_cell_matching=True, mode=TableFormerMode.FAST
        ),
        ocr_options=OcrAutoOptions(lang=["eng"], force_full_page_ocr=False),
        # Process pages in batches to bound peak VRAM usage on large documents.
        # Tune via PDF_BATCH_SIZE env var if OOM persists; lower = less VRAM,
        # but more pipeline overhead per document.
        page_batch_size=page_batch_size,
    )
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options)
        }
    )
    return converter.convert(path).document
