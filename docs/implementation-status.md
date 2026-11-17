# RedThread Implementation Status & Repository Audit

> **Document Status**: `DESIGN`  
> **Last Audited**: 2026-11-18  
> **Baseline Commit**: Initial Cognee Hackathon MVP

---

## 1. Repository Audit Summary

A comprehensive line-by-line audit of the existing codebase (`backend/`, `frontend/`, `test/`) was conducted. The current repository represents an early-stage hackathon prototype developed for the Cognee hackathon. It proves that Cognee can index text and traverse edges, but lacks production enterprise engineering, multi-tenancy, authentication, durable relational persistence, and fault tolerance.

### Current State vs. Target State Matrix

| Component | Existing Codebase State | Status Label | Action Required for Target State |
| :--- | :--- | :---: | :--- |
| **Authentication & IAM** | No authentication; all endpoints open to public; no password hashing; no sessions. | `PLANNED` | Build JWT auth (15m access / 7d refresh), Argon2id hashing, and RBAC middleware. |
| **Multi-Tenancy** | Single-tenant demo. No organization or case boundary models. | `PLANNED` | Implement `organizations`, `memberships`, `cases`, `case_members` with RLS. |
| **Data Persistence** | In-memory Python dictionaries (`DATASET_TEXTS`, `EDGE_CONFIDENCE`). All lost on restart! | `REPLACE` | Replace in-memory dicts with PostgreSQL 16 schema managed via SQLAlchemy 2.0 & Alembic. |
| **Ingestion Pipeline** | Synchronous upload in `backend/main.py`; blocking HTTP call to `cognee.remember()`. | `REPLACE` | Build async Celery pipeline with Redis queue, S3 object storage, and outbox event publishing. |
| **Document Parsers** | Only handles raw UTF-8 string decoding (`file.read().decode("utf-8")`). | `PLANNED` | Implement robust parsers: PyMuPDF (PDF), python-docx (DOCX), email (EML), pandas (CSV). |
| **Entity Extraction** | Delegated implicitly to Cognee's internal LLM parser. No custom Pydantic schemas. | `REPLACE` | Implement direct Gemini 1.5 Pro structured extraction with page offsets and bounding spans. |
| **Entity Resolution** | Naive lowercase exact match (`backend/memory.py:find_overlap`). | `REPLACE` | Implement weighted scoring ($S = 0.35N + 0.25A + 0.25C + 0.15T$) and human review queue. |
| **Graph Intelligence** | Calls `cognee.recall()` and extracts flat graph via `backend/graph_transform.py`. | `REFACTOR` | Retain Cognee engine as accelerator; add bounded BFS traversal and path validation against PG. |
| **Claim Lifecycle** | Simulated confidence dictionary; `forget` endpoint deletes entire Cognee dataset. | `REPLACE` | Implement versioned claim state machine (`ACTIVE`, `DISPUTED`, `RETRACTED`) and `claim_events`. |
| **RAG & Synthesis** | Basic prompt in `backend/llm.py` without verifiable citation offsets or ground truth check. | `REFACTOR` | Build 13-stage hybrid retrieval pipeline with strict citation grounding and unanswerable fallback. |
| **Evaluation Suite** | 15 hardcoded QA pairs in `backend/eval/qa_pairs.json` evaluated via `run_eval.py`. | `REFACTOR` | Expand to reproducible 200-question benchmark with development, validation, and test splits. |
| **Frontend UI** | Next.js 15 App with `react-force-graph-2d`, unauthenticated fetch to `localhost:8000`. | `REFACTOR` | Build 3-panel workspace, auth guards, TanStack Query, and claim challenge interface. |
| **Testing** | 6 ad-hoc scripts in `test/`; only `test_overlap.py` has pytest assertions. | `REPLACE` | Comprehensive pytest suite (unit, integration, security, idempotency) and Playwright E2E. |
| **Deployment / CI** | None; runs locally with manual `uvicorn` and `npm run dev`. | `PLANNED` | Docker Compose (API, worker, Postgres, Redis, MinIO), GitHub Actions CI/CD. |

---

## 2. Code Reuse & Refactoring Assessment

### 2.1 Reusable Assets (Keep & Adapt)
1. **Frontend Graph Visualization (`frontend/components/GraphView.tsx`)**:
   - The force-directed graph setup using `react-force-graph-2d` works well and can be adapted to visually render claim dispute styling (amber dashed lines) and path highlights.
2. **Cognee Graph Flattening Utility (`backend/graph_transform.py`)**:
   - The logic in `get_flat_graph()` that reads node and edge objects from Cognee's internal engine is solid and can be wrapped in the Cognee integration adapter.
3. **Core Concept Evaluation Baseline (`backend/eval/run_eval.py`)**:
   - The comparative evaluation structure between vector search (`recall_baseline`) and graph recall (`recall`) provides a working baseline for the expanded 200-question benchmark.

### 2.2 Flawed Assets (Must Be Replaced)
1. **In-Memory Dictionaries (`DATASET_TEXTS`, `EDGE_CONFIDENCE` in `backend/main.py`)**:
   - Must be completely removed. All state must live in PostgreSQL tables (`claims`, `claim_sources`, `claim_events`, `documents`).
2. **Synchronous Ingestion (`POST /ingest/stream` in `backend/main.py`)**:
   - Must be replaced by `POST /api/v1/cases/{id}/documents` with asynchronous Celery task dispatch and SSE status streaming.
3. **Dataset Deletion for "Forgetting" (`cognee.forget(dataset=target)`)**:
   - In real investigations, deleting an entire dataset when a claim is disputed destroys unrelated valid evidence. Must be replaced with claim status transitions (`DISPUTED`, `RETRACTED`).

---

## 3. Module Implementation Progress Tracker

| Module | Design | Implemented | Verified | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Module 01: Auth & Tenancy** | ✅ | ❌ | ❌ | `DESIGN` |
| **Module 02: Case Management** | ✅ | ❌ | ❌ | `DESIGN` |
| **Module 03: Document Ingestion** | ✅ | ⚠️ Partial (sync) | ❌ | `DESIGN` |
| **Module 04: Extraction & Provenance** | ✅ | ⚠️ Partial (Cognee) | ❌ | `DESIGN` |
| **Module 05: Entity Resolution** | ✅ | ⚠️ Partial (exact) | ⚠️ (test_overlap) | `DESIGN` |
| **Module 06: Knowledge Graph** | ✅ | ⚠️ Partial (Cognee) | ❌ | `DESIGN` |
| **Module 07: Hybrid Recall & RAG** | ✅ | ⚠️ Partial (15 QA) | ❌ | `DESIGN` |
| **Module 08: Contradiction & Forgetting**| ✅ | ⚠️ Partial (dict) | ❌ | `DESIGN` |
| **Module 09: Workspace UI** | ✅ | ⚠️ Prototype | ❌ | `DESIGN` |
| **Module 10: Reports & Export** | ✅ | ❌ | ❌ | `DESIGN` |

*(Status will transition from `DESIGN` to `IN_PROGRESS`, `IMPLEMENTED`, and `VERIFIED` strictly following phase execution gates).*
