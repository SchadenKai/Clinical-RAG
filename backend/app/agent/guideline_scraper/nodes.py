import asyncio
import io
import re
from urllib.parse import urlparse

from langgraph.runtime import Runtime

from app.services.scrapper import (
    cdc_pdf_url_list_oai,
    cdc_pdf_url_list_playwright,
    download_pdf_to_bytes,
    who_pdf_url_list,
)

from .context import AgentContext
from .models import PdfRecord, ScraperProgressEnum
from .state import AgentState

_WHO_BASE_URL = "https://www.who.int/publications/i"
_CDC_OAI_URL = "https://stacks.cdc.gov/fedora/oai"
_CDC_PLAYWRIGHT_URL = "https://stacks.cdc.gov/guidelines"
_WHO_HOST = "https://www.who.int"


def who_url_collector_node(state: AgentState) -> dict:
    """
    Collects WHO clinical guideline PDF URLs via Playwright.
    Reuses the existing who_pdf_url_list() function from scrapper.py.
    Handles relative WHO URLs by prepending the base host.
    """
    who_url = state.who_url or _WHO_BASE_URL
    print(f"[INFO] Collecting WHO PDF URLs from: {who_url}")

    raw_urls: set = asyncio.run(who_pdf_url_list(who_url))

    records = []
    for url in raw_urls:
        if not url:
            continue
        # Relative URLs (e.g. "/publications/i/item/...") need the base host prepended
        if not url.startswith("http"):
            url = _WHO_HOST + url
        records.append(PdfRecord(pdf_url=url, source="who"))

    print(f"[INFO] Collected {len(records)} WHO PDF records")
    return {
        "who_pdf_records": records,
        "progress_status": ScraperProgressEnum.COLLECTING_WHO_URLS,
    }


def cdc_url_collector_node(state: AgentState) -> dict:
    """
    Collects CDC STACKS clinical guideline PDF URLs via OAI-PMH API.
    Falls back to Playwright scraper if OAI-PMH returns no results.
    Short-circuits if scrape_cdc=False.
    """
    if not state.scrape_cdc:
        return {"cdc_pdf_records": []}

    cdc_url = state.cdc_url or _CDC_OAI_URL
    print(f"[INFO] Collecting CDC PDF URLs via OAI-PMH from: {cdc_url}")

    raw_records = asyncio.run(cdc_pdf_url_list_oai(base_url=cdc_url))

    if not raw_records:
        print("[WARNING] OAI-PMH returned no records, falling back to Playwright")
        raw_records = asyncio.run(cdc_pdf_url_list_playwright(_CDC_PLAYWRIGHT_URL))

    records = [
        PdfRecord(
            pdf_url=r["pdf_url"],
            title=r.get("title"),
            date=r.get("date"),
            source="cdc",
            identifier=r.get("identifier"),
        )
        for r in raw_records
        if r.get("pdf_url")
    ]

    print(f"[INFO] Collected {len(records)} CDC PDF records")
    return {
        "cdc_pdf_records": records,
        "progress_status": ScraperProgressEnum.COLLECTING_CDC_URLS,
    }


def merge_records_node(state: AgentState) -> dict:
    """
    Merges WHO and CDC PDF records into a single deduplicated list.
    Respects the scrape_who / scrape_cdc flags.
    """
    all_records: list[PdfRecord] = []
    seen_urls: set[str] = set()

    sources: list[PdfRecord] = []
    if state.scrape_who and state.who_pdf_records:
        sources.extend(state.who_pdf_records)
    if state.scrape_cdc and state.cdc_pdf_records:
        sources.extend(state.cdc_pdf_records)

    for record in sources:
        if record.pdf_url not in seen_urls:
            seen_urls.add(record.pdf_url)
            all_records.append(record)

    print(f"[INFO] Merged {len(all_records)} unique PDF records")
    return {
        "all_pdf_records": all_records,
        "progress_status": ScraperProgressEnum.MERGING_RECORDS,
    }


def download_and_upload_node(state: AgentState, runtime: Runtime[AgentContext]) -> dict:
    """
    Downloads each PDF and uploads it to MinIO S3.

    MinIO key format: raw-pdfs/{source}/{sanitized_filename}.pdf
    Uses list_objects_v2 pagination to pre-fetch existing keys for deduplication.
    Uses io.BytesIO + upload_fileobj for in-memory uploads.
    """
    s3_client = runtime.context.s3_service.client
    bucket = runtime.context.settings.minio_bucket_name

    # Pre-fetch existing keys to enable idempotent runs
    existing_keys: set[str] = set()
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix="raw-pdfs/"):
            for obj in page.get("Contents", []):
                existing_keys.add(obj["Key"])
        print(f"[INFO] Found {len(existing_keys)} existing objects in MinIO")
    except Exception as e:
        print(f"[WARNING] Could not list existing objects in MinIO: {e}")

    uploaded_keys: list[str] = []
    failed_urls: list[str] = []
    skipped_urls: list[str] = []

    all_records = state.all_pdf_records or []
    print(f"[INFO] Processing {len(all_records)} PDF records")

    for record in all_records:
        filename = _derive_filename(record)
        minio_key = f"raw-pdfs/{record.source}/{filename}"

        # Dedup: skip if already uploaded
        if minio_key in existing_keys:
            print(f"[SKIP] Already exists in MinIO: {minio_key}")
            skipped_urls.append(record.pdf_url)
            continue

        # Download PDF
        pdf_bytes = asyncio.run(download_pdf_to_bytes(record.pdf_url))
        if pdf_bytes is None:
            print(f"[FAIL] Could not download: {record.pdf_url}")
            failed_urls.append(record.pdf_url)
            continue

        # Upload to MinIO
        try:
            file_obj = io.BytesIO(pdf_bytes)
            s3_client.upload_fileobj(
                file_obj,
                bucket,
                minio_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )
            uploaded_keys.append(minio_key)
            print(f"[OK] Uploaded: {minio_key}")
        except Exception as e:
            print(f"[FAIL] Upload error for {minio_key}: {e}")
            failed_urls.append(record.pdf_url)

    print(
        f"[INFO] Done. Uploaded: {len(uploaded_keys)}, "
        f"Failed: {len(failed_urls)}, Skipped: {len(skipped_urls)}"
    )
    return {
        "uploaded_keys": uploaded_keys,
        "failed_urls": failed_urls,
        "skipped_urls": skipped_urls,
        "progress_status": ScraperProgressEnum.DONE,
        "run_metadata": {
            "total_records": len(all_records),
            "uploaded": len(uploaded_keys),
            "failed": len(failed_urls),
            "skipped": len(skipped_urls),
        },
    }


def _derive_filename(record: PdfRecord) -> str:
    """Derive a safe MinIO filename from a PdfRecord's URL."""
    path = urlparse(record.pdf_url).path
    filename = path.rstrip("/").split("/")[-1]
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    # Replace any non-alphanumeric chars (except hyphens and dots) with underscores
    filename = re.sub(r"[^\w\-.]", "_", filename)
    return filename
