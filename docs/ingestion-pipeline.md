# RedThread Document Ingestion Pipeline

> **Document Status**: `DESIGN`  
> **Core Pipeline**: Asynchronous, reliable document ingestion, structured LLM extraction, transactional outbox publishing, and idempotent graph synchronization.

---

## 1. Overview & Architecture

The ingestion pipeline transforms raw, heterogeneous investigative documents into structured, interconnected, and verifiable knowledge graph entities and claims. Because document parsing, chunking, LLM extraction, and graph synchronization take from several seconds to minutes per document, all processing is performed **asynchronously** via background Celery workers, Redis, and a transactional outbox.

---

## 2. Ingestion Lifecycle & Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Client as Investigator / UI
    participant API as FastAPI /api/v1
    participant S3 as Object Storage (S3/R2)
    participant PG as PostgreSQL 16
    participant Relay as Outbox Publisher
    participant Redis as Redis Broker
    participant Worker as Celery Worker
    participant LLM as Gemini 1.5 Pro
    participant Cognee as Cognee Engine

    Client->>API: POST /cases/{id}/documents (multipart/form-data)
    API->>API: Validate MIME magic bytes & compute SHA-256
    API->>S3: Upload raw file payload
    Note over API,PG: Single Database Transaction
    API->>PG: Insert Document & IngestionJob (status: QUEUED)
    API->>PG: Insert OutboxEvent (DOCUMENT_INGESTION_REQUESTED)
    API-->>Client: 202 Accepted {job_id, document_id, status: "QUEUED"}
    
    Relay->>PG: Poll PENDING OutboxEvents
    Relay->>Redis: Publish job to celery queue
    Relay->>PG: Mark OutboxEvent as PUBLISHED
    
    Worker->>Redis: Consume task message
    Worker->>PG: Update IngestionJob (status: PROCESSING)
    Worker->>S3: Download document bytes
    Worker->>Worker: Parse text (PyMuPDF/docx/email/pandas)
    Worker->>PG: Persist DocumentChunks with offsets & token counts
    Worker->>LLM: Request structured extraction (Entities, Claims, Offsets)
    LLM-->>Worker: Validated Pydantic Extraction Payload
    Worker->>Worker: Run Entity Resolution & Alias Linking
    Worker->>PG: Insert Entities, Claims, ClaimSources
    Worker->>Cognee: Sync graph nodes & edges (Idempotent)
    Worker->>PG: Update IngestionJob (status: COMPLETED)
    Worker-->>Client: Real-time update (SSE / Polling)
```

---

## 3. Ingestion State Machine

The document ingestion job adheres to a strictly defined state machine ensuring resiliency and recoverability:

```mermaid
stateDiagram-v2
    [*] --> QUEUED : Document uploaded & outbox event committed
    QUEUED --> PROCESSING : Worker acquires job lock
    PROCESSING --> COMPLETED : Extraction & Cognee sync successful
    PROCESSING --> FAILED : Transient exception (Timeout / RateLimit)
    FAILED --> RETRYING : Attempt < Max Attempts (Exponential Backoff)
    RETRYING --> PROCESSING : Retry execution
    FAILED --> DEAD_LETTER : Attempt >= Max Attempts (Alert generated)
    DEAD_LETTER --> [*] : Requires manual inspection / retry API
    COMPLETED --> [*]
```

### State Definitions
* **`QUEUED`**: Metadata written to PostgreSQL, file stored in S3, outbox event published to Redis.
* **`PROCESSING`**: Worker has acquired the Redis distributed lock (`lock:document:{document_id}`) and is executing parsing or extraction.
* **`COMPLETED`**: Chunks, entities, claims, and sources committed to PostgreSQL, and nodes/edges synchronized to Cognee.
* **`FAILED`**: A transient error occurred (Gemini 429, network timeout).
* **`RETRYING`**: Job awaiting exponential backoff delay before re-entering `PROCESSING`.
* **`DEAD_LETTER`**: Reached maximum retry count (default: 3). Alert generated in `audit_logs`.

---

## 4. Multi-Format Parsers

RedThread supports four primary document formats with granular page and offset tracking:

| Format | Library | Extraction Strategy | Offset Preservation |
| :--- | :--- | :--- | :--- |
| **PDF** | `PyMuPDF` (`fitz`) | Direct page text extraction with layout awareness. Handles multi-column layouts and scans with OCR fallback. | Page number + character start/end index within the page. |
| **DOCX** | `python-docx` | Structured paragraph and table cell traversal. | Paragraph index + character offset. |
| **TXT / MD**| Standard I/O + `chardet` | Character encoding auto-detection (UTF-8, Latin-1) and line normalization. | Global character start/end offset. |
| **EML** | Python `email` module | Extracts headers (From, To, CC, Subject, Date) and parses plain-text/HTML message bodies. | Header boundaries + body character offsets. |
| **CSV** | `pandas` / `csv` | Tabular row-by-row parsing, generating contextualized natural-language row sentences for extraction. | Row index + column header references. |

---

## 5. Structured Extraction with Gemini & Pydantic

During stage 6 of ingestion, chunks (typically 1,500 tokens with 200 token overlap) are processed by Gemini using structured output schemas:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedEntity(BaseModel):
    name: str = Field(description="Observed entity name in text")
    entity_type: str = Field(description="PERSON, ORGANIZATION, FINANCIAL_ACCOUNT, MONETARY_AMOUNT, etc.")

class ExtractedClaim(BaseModel):
    subject: str = Field(description="Subject entity name")
    predicate: str = Field(description="Action or relationship, e.g., TRANSFERRED_TO, OWNS, EMPLOYED_BY")
    target_entity: Optional[str] = Field(None, description="Target entity if object is an entity")
    target_value: Optional[str] = Field(None, description="Literal value if object is a literal (e.g. $50,000)")
    quoted_text: str = Field(description="Exact verbatim excerpt from document supporting this claim")
    page_number: int = Field(description="1-based page number")
    start_offset: int = Field(description="Character start offset in chunk")
    end_offset: int = Field(description="Character end offset in chunk")
    confidence: float = Field(description="Model extraction confidence score (0.0 to 1.0)")

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    claims: List[ExtractedClaim]
```

### Epistemic Boundary Rule:
> [!IMPORTANT]
> An LLM-extracted relationship is **never treated as ground truth**. It is recorded in PostgreSQL as an **attributed claim** with its source citation. Only human investigators or verified corroborating evidence can promote or review the claim's status.

---

## 6. Fault Tolerance, Idempotency & Recovery

1. **SHA-256 Content Deduplication**: Before processing, the document's SHA-256 hash is checked against the target case. If a duplicate is detected, the upload references the existing document, avoiding redundant LLM inference costs.
2. **Distributed Job Locks**: Workers acquire a Redis lock on `lock:document:{document_id}` with a TTL of 10 minutes to prevent dual execution by concurrent workers.
3. **Transactional Database Commits**: All chunks, entities, claims, and sources for a document are committed within a single database transaction. If the worker crashes halfway through, the transaction rolls back cleanly.
4. **Idempotent Cognee Synchronization**: Graph nodes and edges are synchronized with deterministic UUIDs. Re-running synchronization on a retried job updates existing nodes without creating duplicates.
5. **Exponential Backoff**:
   $$\text{Delay}(t) = \text{base\_delay} \times 2^{\text{attempt}} + \text{jitter}$$
   Default: 5 seconds base delay $\rightarrow$ 10s $\rightarrow$ 20s $\rightarrow$ Dead letter.

---

## 7. Related Documents
- [System Architecture](architecture.md)
- [Database Design](database-design.md)
- [Data Consistency](data-consistency.md)
- [ADR-002: Asynchronous Ingestion](decisions/ADR-002-asynchronous-ingestion-pipeline.md)
