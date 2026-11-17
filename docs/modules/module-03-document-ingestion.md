# Module 3: Document Ingestion Pipeline

## 1. Purpose & Scope
The Ingestion Pipeline is the asynchronous engine responsible for taking raw, heterogeneous files (PDFs, Word documents, emails, spreadsheets, text memos), validating their integrity, storing them in object storage, chunking their contents, invoking Gemini for structured extraction, and populating PostgreSQL and the Cognee graph engine.

---

## 2. Supported Formats & Parsing Strategies
- **PDF**: PyMuPDF (`fitz`) handles complex multi-column reports and extracts exact page boundaries.
- **DOCX**: `python-docx` extracts paragraphs, tables, and hierarchical headings.
- **TXT / MD**: Unicode normalization and line offset tracking.
- **EML**: Python `email` parser extracts sender, recipient, CC, timestamp, and message body.
- **CSV**: `pandas` converts structured tabular records into contextualized statements with row citations.

---

## 3. Ingestion State Machine

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> PROCESSING
    PROCESSING --> COMPLETED
    PROCESSING --> FAILED
    FAILED --> RETRYING : Attempts < 3
    RETRYING --> PROCESSING
    FAILED --> DEAD_LETTER : Attempts >= 3
```

---

## 4. Key Production Requirements
1. **Asynchronous Decoupling**: API upload returns immediately with `202 Accepted` and a `job_id`.
2. **PostgreSQL as State Authority**: Redis acts purely as the message queue transport; persistent job status and attempt history reside in `ingestion_jobs`.
3. **SHA-256 Deduplication**: Files with identical hashes in the same case are deduplicated immediately.
4. **Idempotency**: Workers use distributed locks and single-transaction commits so retried jobs never create duplicate entities or claims.
5. **Detailed Documentation**: See the comprehensive [Ingestion Pipeline Specification](file:///home/rushikeshbathe096/hackathons/Redthread/docs/ingestion-pipeline.md) and [ADR-002](file:///home/rushikeshbathe096/hackathons/Redthread/docs/decisions/ADR-002-asynchronous-ingestion-pipeline.md).
