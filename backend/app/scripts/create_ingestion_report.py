import uuid

from app.data.test_web_sources import urls
from app.routes.dependencies.rag import get_indexing_service_manual

md_report_template = """
## Result no. {result_number}
URL: {website_url}

### Raw Doc: 
```
{raw_docs_page_content}
```

### Chunked Docs: 
{chunked_docs}

### Run Metadata: 
{run_metadata}
\n\n
"""

chunked_docs_template = """
---
Page Content no. {index}:
```
{page_content} 
```

Metadata: 
```
{metadata}
```
"""

indexing_agent = get_indexing_service_manual()
for idy, url in enumerate(urls, start=0):
    print("Starting ingestion of website")
    res_state = indexing_agent.ingest_document(
        website_url=url, request_id=str(uuid.uuid4())
    )
    file_path = "app/data/reports/ingestion_pipeline_report.md"
    print("Creating file named ingestion_pipeline_report.md")

    chunked_docs_final_string = ""
    for idx, doc in enumerate(res_state["chunked_documents"], start=0):
        chunked_docs_final_string += chunked_docs_template.format(
            index=idx + 1, page_content=doc.page_content, metadata=doc.metadata
        )

    with open(file=file_path, mode="a") as file:
        file.writelines(
            md_report_template.format(
                result_number=idy + 1,
                website_url=res_state["website_url"],
                raw_docs_page_content=res_state["raw_document"][0].page_content,
                chunked_docs=chunked_docs_final_string,
                run_metadata=res_state["run_metadata"],
            )
        )

    print("Written the report to the markdown file. Closing the file...")
print("Done")
