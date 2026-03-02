from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument


def document_extractor(path: Path) -> DoclingDocument:
    doc_converter = DocumentConverter()
    return doc_converter.convert(path).document
