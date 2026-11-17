# ADR-002: Asynchronous Job-Based Document Ingestion Pipeline

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
Document ingestion involves file format parsing (PyMuPDF for multi-page PDFs, python-docx, email headers), text chunking, LLM extraction calls (Gemini 1.5 Pro), entity resolution scoring, database writes, and Cognee graph synchronization.

For a 50-page investigative report, processing duration typically spans between 15 and 90 seconds. Keeping an HTTP connection open across this lifecycle creates several severe engineering issues:
- HTTP client timeouts (reverse proxies drop connections after 30–60s).
- Exhaustion of web server worker threads.
- Inability to safely retry transient failures without forcing the user to re-upload.

## Decision
We decouple file upload from processing using an **asynchronous job architecture** backed by **PostgreSQL (state persistence)**, **Transactional Outbox**, **Redis (task transport)**, and **Celery (worker execution)**.

### Operational Lifecycle:
1. **Synchronous Upload Endpoint**:
   - Accepts file via `POST /api/v1/cases/{id}/documents`.
   - Validates MIME type magic bytes, calculates SHA-256 hash.
   - Uploads binary payload to S3-compatible storage.
   - Writes `documents`, `ingestion_jobs` (`status: QUEUED`), and `outbox_events` (`status: PENDING`) in a single database transaction.
   - Responds immediately with HTTP 202 Accepted and job ID.
2. **Transactional Outbox Publisher**:
   - Reads pending outbox records and enqueues task messages to Redis.
3. **Asynchronous Worker**:
   - Celery worker pulls job, transitions state to `PROCESSING`.
   - Executes multi-stage pipeline: Parse $\rightarrow$ Chunk $\rightarrow$ LLM Extract $\rightarrow$ Resolve $\rightarrow$ Persist $\rightarrow$ Cognee Sync.
   - Commits transactional updates and transitions job to `COMPLETED`.
4. **Resilience & Retries**:
   - State machine handles `RETRYING` with exponential backoff on transient errors.
   - Hard cap of 3 retry attempts before transitioning to `DEAD_LETTER`.

## Consequences
- **Positive**: Immediate HTTP response times (p95 $< 1000\text{ ms}$); resilient background processing; outbox guarantees reliable task dispatch.
- **Negative**: Introduces Redis and Celery infrastructure dependencies; requires polling or Server-Sent Events (SSE) on the frontend.

---

## Related Documents
- [Document Ingestion](../ingestion-pipeline.md)
- [System Architecture](../architecture.md)
- [Data Consistency](../data-consistency.md)
