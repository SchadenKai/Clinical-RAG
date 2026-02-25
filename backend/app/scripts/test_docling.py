from docling.chunking import HierarchicalChunker

from app.routes.dependencies.file_store import get_s3_service
from app.routes.dependencies.settings import get_app_settings
from app.services.scrapper import document_extractor

_FILE_NAME = (
    "/Users/kairusnoahtecson/Documents/Github/"
    "cdc-who-guideline-rag-service/backend/app/scripts/9789240115774-eng.pdf"
)

app_settings = get_app_settings()
s3_service = get_s3_service(app_settings)


doc = document_extractor(_FILE_NAME)
chunks = doc.texts
print(f"Initial number of chunks: {len(chunks)}")
chunker = HierarchicalChunker(always_emit_headings=True, merge_list_items=True)
chunks = chunker.chunk(doc)
chunks = list(chunks)
print(f"Number of chunks after hierachal chunking: {len(chunks)}")
