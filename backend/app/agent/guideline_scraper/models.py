import enum
from typing import Optional

from pydantic import BaseModel


class ScraperProgressEnum(enum.Enum):
    COLLECTING_WHO_URLS = "Collecting WHO PDF URLs"
    COLLECTING_CDC_URLS = "Collecting CDC PDF URLs"
    MERGING_RECORDS = "Merging Records"
    DOWNLOADING_AND_UPLOADING = "Downloading and Uploading PDFs"
    DONE = "Done"


class PdfRecord(BaseModel):
    pdf_url: str
    title: Optional[str] = None
    date: Optional[str] = None
    source: str  # "who" | "cdc"
    identifier: Optional[str] = None
