from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.agent.guideline_scraper.models import PdfRecord, ScraperProgressEnum


class AgentState(BaseModel):
    # Which sources to scrape
    scrape_who: bool = True
    scrape_cdc: bool = True

    # Optional URL overrides (use production defaults if None)
    who_url: Optional[str] = None  # defaults to "https://www.who.int/publications/i"
    cdc_url: Optional[str] = None  # defaults to OAI-PMH endpoint

    # Collected PDF metadata from each source
    who_pdf_records: Optional[list[PdfRecord]] = None
    cdc_pdf_records: Optional[list[PdfRecord]] = None

    # Combined deduplicated list after merge
    all_pdf_records: Optional[list[PdfRecord]] = None

    # Upload results
    uploaded_keys: Optional[list[str]] = None   # MinIO object keys successfully uploaded
    failed_urls: Optional[list[str]] = None     # URLs that failed download or upload
    skipped_urls: Optional[list[str]] = None    # URLs already present in MinIO (dedup)

    progress_status: Optional[ScraperProgressEnum] = None
    run_metadata: Optional[dict] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
