import json
import os

os.environ["TORCH_COMPILE_DISABLE"] = "1"
from docling.chunking import HierarchicalChunker, HybridChunker

from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.settings import get_app_settings
from app.services.scrapper import document_extractor

_FILE_NAME = "Galaxy - Wikipedia.pdf"
MD_FILE_DEST = "test_md_1.md"
HIERARCHAL_RESULTS_DEST = "hierarchal_chunking.json"
HYBRID_RESULTS_DEST = "hybrid_chunking_batch_1.json"
DOCLING_DOCUMENT_DEST = "docling_document.json"

app_settings = get_app_settings()
s3_service = get_s3_service(app_settings)
tokenizer_service = get_tokenizer_service(app_settings)

with S3FileStager(
    s3_service=s3_service, file_key=_FILE_NAME, settings=app_settings
) as file_path:
    doc = doc_converter(file_path)
    with open(file=DOCLING_DOCUMENT_DEST, mode="w", encoding="utf-8") as f:
        json.dump(doc, f, indent=4, ensure_ascii=False)
    
    md_text = doc.export_to_markdown()
    with open(file=MD_FILE_DEST, mode="w", encoding="utf-8") as f:
        f.write(md_text)

    hierarchal_chunker = HierarchicalChunker(
        always_emit_headings=True, merge_list_items=True
    )
    chunks = hierarchal_chunker.chunk(doc)
    serializable_chunks = [chunk.model_dump() for chunk in chunks]
    with open(file=HIERARCHAL_RESULTS_DEST, mode="w", encoding="utf-8") as f:
        json.dump(serializable_chunks, f, indent=4, ensure_ascii=False)

    tokenizer = tokenizer_service.embedding_tokenizer
    hybrid_chunker = HybridChunker(tokenizer=tokenizer, max_tokens=512)
    chunks_1 = hybrid_chunker.chunk(doc)
    serializable_chunks = [chunk.model_dump() for chunk in chunks_1]
    with open(file=HYBRID_RESULTS_DEST, mode="w", encoding="utf-8") as f:
        json.dump(serializable_chunks, f, indent=4, ensure_ascii=False)
