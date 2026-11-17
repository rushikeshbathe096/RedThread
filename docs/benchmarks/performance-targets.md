# RedThread Engineering Performance Targets & SLAs

## 1. Latency Budgets (Under Standard Load)

Latency targets are specified for standard testing conditions (PostgreSQL with connection pooling, Redis caching, and cold network hops excluded):

| Operation | Target Percentile | Target Budget | Notes |
| :--- | :---: | :---: | :--- |
| **Standard CRUD API Call** | p95 | $< 300\text{ ms}$ | Cases, users, document metadata listing. |
| **Dashboard Metrics Read** | p95 | $< 500\text{ ms}$ | Case activity, claim status distribution, recent events. |
| **Document Upload Acknowledgment** | p95 | $< 1000\text{ ms}$ | MIME verification, SHA-256 hash, S3 write, queue enqueue. |
| **Graph Subgraph Retrieval** | p95 | $< 1000\text{ ms}$ | Bounded 2-hop neighborhood expansion ($< 500$ nodes/edges). |
| **Cached Entity & Alias Lookup** | p95 | $< 100\text{ ms}$ | Redis-cached entity resolution and canonical name check. |
| **Intelligent Recall: Retrieval Stage** | p95 | $< 1200\text{ ms}$ | Combined BFS graph traversal + vector similarity search. |
| **Intelligent Recall: LLM Generation** | p95 | $< 2500\text{ ms}$ | Gemini 1.5 Pro streaming response initiation. |

---

## 2. Ingestion Throughput & Concurrency

| Metric | Target Specification |
| :--- | :--- |
| **Worker Concurrency** | 4–8 concurrent Celery worker processes per instance. |
| **Document Throughput** | Minimum 15 multi-page documents (avg. 20 pages) per worker per minute. |
| **Rate Limit Management** | Token-bucket rate limiter for Gemini API calls to prevent 429 errors. |
| **Job Timeout** | Hard timeout of 300 seconds per document task before killing worker process. |

---

## 3. Reliability & Fault Recovery

1. **Worker Crash Recovery**: If a Celery worker dies mid-extraction, Celery's `acks_late=True` policy ensures the job message is redelivered to an active worker.
2. **Partial Write Prevention**: Database updates for entities, claims, and sources are encapsulated in a single database transaction (`BEGIN ... COMMIT`). Failed extraction attempts trigger an automatic rollback.
3. **Database Connection Pooling**:
   - SQLAlchemy `AsyncEngine` pool size: 20 connections.
   - Max overflow: 10 connections.
   - Pool timeout: 30 seconds.
   - Pool recycle: 1800 seconds.
