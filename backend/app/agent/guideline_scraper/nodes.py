import hashlib
import io
import re
from urllib.parse import urlparse

from langgraph.runtime import Runtime

from app.logger import app_logger
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


async def who_url_collector_node(state: AgentState) -> dict:
    """
    Collects WHO clinical guideline PDF URLs via Playwright.
    Reuses the existing who_pdf_url_list() function from scrapper.py.
    Handles relative WHO URLs by prepending the base host.
    """
    who_url = state.who_url or _WHO_BASE_URL
    app_logger.info("Collecting WHO PDF URLs from: %s", who_url)

    raw_urls: set = await who_pdf_url_list(who_url)

    records = []
    for url in raw_urls:
        if not url:
            continue
        # Relative URLs (e.g. "/publications/i/item/...") need the base host prepended
        if not url.startswith("http"):
            url = _WHO_HOST + url
        records.append(PdfRecord(pdf_url=url, source="who"))

    app_logger.info("Collected %d WHO PDF records", len(records))
    return {
        "who_pdf_records": records,
        "progress_status": ScraperProgressEnum.COLLECTING_WHO_URLS,
    }


async def cdc_url_collector_node(state: AgentState) -> dict:
    """
    Collects CDC STACKS clinical guideline PDF URLs via OAI-PMH API.
    Falls back to Playwright scraper if OAI-PMH returns no results.
    Short-circuits if scrape_cdc=False.
    """
    if not state.scrape_cdc:
        return {"cdc_pdf_records": []}

    cdc_url = state.cdc_url or _CDC_OAI_URL
    app_logger.info("Collecting CDC PDF URLs via OAI-PMH from: %s", cdc_url)

    raw_records = await cdc_pdf_url_list_oai(base_url=cdc_url)

    if not raw_records:
        app_logger.warning("OAI-PMH returned no records, falling back to Playwright")
        raw_records = await cdc_pdf_url_list_playwright(_CDC_PLAYWRIGHT_URL)

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

    app_logger.info("Collected %d CDC PDF records", len(records))
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

    app_logger.info("Merged %d unique PDF records", len(all_records))
    return {
        "all_pdf_records": all_records,
        "progress_status": ScraperProgressEnum.MERGING_RECORDS,
    }


async def download_and_upload_node(
    state: AgentState, runtime: Runtime[AgentContext]
) -> dict:
    """
    Downloads each PDF and uploads it to MinIO S3.

    MinIO key format: raw-pdfs/{source}/{sanitized_filename}.pdf
    Uses list_objects_v2 pagination to pre-fetch existing keys for deduplication.
    Uses io.BytesIO + upload_fileobj for in-memory uploads.
    On filename collision within a run, appends a short sha256 hash suffix.
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
        app_logger.info("Found %d existing objects in MinIO", len(existing_keys))
    except Exception as e:
        app_logger.warning("Could not list existing objects in MinIO: %s", e)

    uploaded_keys: list[str] = []
    failed_urls: list[str] = []
    skipped_urls: list[str] = []
    uploaded_this_run: set[str] = set()

    all_records = state.all_pdf_records or []
    app_logger.info("Processing %d PDF records", len(all_records))

    for record in all_records:
        filename = _derive_filename(record)
        minio_key = f"raw-pdfs/{record.source}/{filename}"

        # Dedup: skip if already uploaded in a previous run
        if minio_key in existing_keys:
            app_logger.info("Skipping already-existing MinIO key: %s", minio_key)
            skipped_urls.append(record.pdf_url)
            continue

        # Download PDF
        pdf_bytes = await download_pdf_to_bytes(record.pdf_url)
        if pdf_bytes is None:
            app_logger.warning("Could not download PDF: %s", record.pdf_url)
            failed_urls.append(record.pdf_url)
            continue

        # Collision: same derived key already uploaded THIS run → suffix with content hash
        if minio_key in uploaded_this_run:
            content_hash = hashlib.sha256(pdf_bytes).hexdigest()[:8]
            if minio_key.endswith(".pdf"):
                minio_key = minio_key[:-4] + f"_{content_hash}.pdf"
            else:
                minio_key = minio_key + f"_{content_hash}"
            app_logger.info(
                "Key collision detected — using hash-suffixed key: %s", minio_key
            )

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
            uploaded_this_run.add(minio_key)
            app_logger.info("Uploaded: %s", minio_key)
        except Exception as e:
            app_logger.error("Upload error for %s: %s", minio_key, e)
            failed_urls.append(record.pdf_url)

    app_logger.info(
        "Done. Uploaded: %d, Failed: %d, Skipped: %d",
        len(uploaded_keys),
        len(failed_urls),
        len(skipped_urls),
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
    """Derive a safe MinIO filename from a PdfRecord's URL.

    Falls back to a deterministic sha256-based name when the URL path has no
    meaningful last segment (empty string or dots only), ensuring MinIO keys
    like raw-pdfs/who/.pdf are never produced.
    """
    path = urlparse(record.pdf_url).path
    filename = path.rstrip("/").split("/")[-1]

    # Guard: empty or dot-only segment → use a short deterministic hash of the URL
    if not filename or all(c == "." for c in filename):
        filename = hashlib.sha256(record.pdf_url.encode()).hexdigest()[:8]

    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    # Replace any non-alphanumeric chars (except hyphens and dots) with underscores
    filename = re.sub(r"[^\w\-.]", "_", filename)
    return filename
