# RedThread Engineering Performance Targets & SLAs

> **Document Status**: `DESIGN`  
> **Engineering Baseline**: Measurable targets under defined hardware and workload conditions. Target values represent engineering budgets, not guaranteed production metrics.

---

## 1. Engineering Target Matrix

| Metric | Target Specification | Measurement Condition |
| :--- | :---: | :--- |
| **Median Retrieval Latency** | $< 500\text{ ms}$ | Combined BFS graph traversal + vector similarity search (p50). |
| **End-to-End Median Query Latency** | $< 2.5\text{ seconds}$ | Complete recall request: query parse + dual retrieval + Gemini synthesis (p50). |
| **p95 Query Latency** | $< 5.0\text{ seconds}$ | 95th percentile under 10 concurrent investigators. |
| **Document Ingestion Throughput** | $\ge 5\text{ docs/minute}$ | Multi-page investigative reports (avg. 20 pages) per 4-worker instance. |
| **Query Latency Improvement** | $\ge 20\%$ | Latency reduction achieved by Redis caching of frequent entity subgraphs. |
| **Investigation Time Reduction** | $\ge 25\%$ | Reduction in manual cross-referencing time demonstrated in human trials. |

---

## 2. API Latency Budgets (Under Standard Load)

| Endpoint / Operation | Target Percentile | Target Budget | Notes |
| :--- | :---: | :---: | :--- |
| **Standard CRUD API** | p95 | $< 300\text{ ms}$ | Cases, users, document metadata listing. |
| **Dashboard Metrics Read** | p95 | $< 500\text{ ms}$ | Activity rollup, claim status counts, dispute alerts. |
| **Document Upload Acknowledgment** | p95 | $< 1000\text{ ms}$ | Validation, SHA-256 hash, S3 write, outbox commit. |
| **Graph Subgraph Retrieval** | p95 | $< 1000\text{ ms}$ | Bounded 2-hop neighborhood ($< 500$ nodes/edges). |
| **Cached Entity & Alias Lookup** | p95 | $< 100\text{ ms}$ | Redis-cached canonical entity resolution. |

---

## 3. Benchmark Environment Specification

To ensure reproducibility, all performance evaluations must document the following hardware and environment parameters:
- **Compute**: 4 vCPU, 16 GB RAM (Linux kernel 6.x).
- **Database**: PostgreSQL 16 on NVMe SSD, connection pool size: 20, max overflow: 10.
- **Cache / Broker**: Redis 7 on local network ($< 1\text{ ms}$ roundtrip).
- **Workers**: Celery 5.4+ with 4 concurrent worker processes (`-c 4`).
- **LLM**: Google Gemini 1.5 Pro via official SDK (`google-genai`).
- **Test Workload**: 50 synthetic PDF files (10 to 50 pages each) uploaded concurrently across 5 simulated case workspaces.

---

## 4. Related Documents
- [Evaluation Framework](evaluation-framework.md)
- [System Architecture](../architecture.md)
- [Testing Strategy](../testing-strategy.md)
- [Deployment & Operations](../deployment-and-operations.md)
