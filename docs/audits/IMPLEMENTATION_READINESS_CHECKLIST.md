# RedThread Implementation Readiness & Quality Gate Checklist

> **Checklist Status**: `ACTIVE`  
> **Target Version**: RedThread 1.0 Production Architecture  
> **Repository Target**: `rushikeshbathe096/RedThread` on `main`  
> **Authoritative Specification**: [Final Documentation Audit](FINAL_DOCUMENTATION_AUDIT.md)

---

## 1. Quality Gate Architecture & Execution Rules

To ensure that RedThread transitions smoothly from specification to production without regressions, implementation is partitioned into **8 sequential phases (Phase 0 through Phase 7)**.

### Strict Governance Rules:
1. **Zero Skipping of Gates**: No phase may begin until the preceding phase’s Acceptance Gate has been formally verified and all checklist items marked complete.
2. **Automated Verification**: Every checklist item specifies an objective verification command or criterion. Manual assumptions or visual assertions alone are prohibited.
3. **No Dead-End Prototyping**: Application code must strictly adhere to the modular monolith structure (`api/`, `services/`, `repositories/`, `models/`, `workers/`).
4. **Relational Authority**: In-memory state dictionaries are strictly banned. All operational state must reside in PostgreSQL 16.

---

## 2. Phase-by-Phase Readiness & Acceptance Gates

### 🟢 Phase 0: Repository Foundation & Test Baselines (Week 1)
*Goal: Stand up local infrastructure, clean up prototype code, configure async database engines, and establish test baselines.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **0.1 Environment Config** | Pydantic `BaseSettings` (`backend/app/config.py`) loads `.env` cleanly with validation for DB URLs, Redis, MinIO, and Gemini API keys. | `python -c "from backend.app.config import settings; print(settings.APP_ENV)"` | ⬜ PENDING |
| **0.2 Docker Infrastructure** | `docker compose up -d` boots PostgreSQL 16, Redis 7, and MinIO without port collisions or restarts. | `docker compose -f infrastructure/docker-compose.yml ps` | ⬜ PENDING |
| **0.3 Async DB Engine** | SQLAlchemy 2.0 `create_async_engine` connects to PostgreSQL with pool size 20, max overflow 10. | `pytest backend/tests/integration/test_db_connection.py` | ⬜ PENDING |
| **0.4 Alembic Harness** | Alembic initialized with `async_engine`, supports `op.get_context().autocommit_block()`. | `alembic upgrade head && alembic downgrade base` | ⬜ PENDING |
| **0.5 Schema Migration** | Initial Alembic migration deploys all 18 PostgreSQL tables, composite keys, constraints, triggers, and RLS policies. | `psql -h localhost -U postgres -d redthread -c "\dt"` (18 tables listed) | ⬜ PENDING |
| **0.6 Structured Logging** | JSON logging configured with correlation ID tracing per request. | `pytest backend/tests/unit/test_logging.py` | ⬜ PENDING |
| **0.7 Test Baseline Harness** | Pytest harness running with async fixtures, transaction rollbacks, and coverage reporting. | `pytest backend/tests/unit/` | ⬜ PENDING |

*Phase 0 Acceptance Gate*: Docker Compose boots cleanly, Alembic migrates forward and backward without error, and baseline unit tests pass with zero warnings.

---

### ⚪ Phase 1: Authentication & Multi-Tenancy (Week 2)
*Goal: Implement cryptographic authentication, JWT session lifecycle, multi-tenant organization boundaries, and PostgreSQL Row-Level Security.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **1.1 Argon2id Hashing** | Passwords hashed using Argon2id with recommended memory and parallelism parameters. | `pytest backend/tests/unit/test_crypto.py` | ⬜ GATED |
| **1.2 JWT Session Lifecycle** | Short-lived access tokens (15m) + rotating refresh tokens (7d) stored as SHA-256 hashes. | `pytest backend/tests/integration/test_auth_tokens.py` | ⬜ GATED |
| **1.3 Refresh Token Rotation** | Reusing a consumed refresh token immediately revokes the entire token family. | `pytest backend/tests/security/test_token_reuse.py` | ⬜ GATED |
| **1.4 Organization & Case APIs** | CRUD endpoints for `/api/v1/organizations` and `/api/v1/cases` enforce role boundaries. | `pytest backend/tests/integration/test_organization_api.py` | ⬜ GATED |
| **1.5 Case Membership RBAC** | Investigators only see cases explicitly assigned via `case_members`. Admin sees all org cases. | `pytest backend/tests/security/test_case_rbac.py` | ⬜ GATED |
| **1.6 Non-Disclosing 404s** | Requesting an unauthorized case UUID returns `404 Not Found`, not `403 Forbidden`. | `pytest backend/tests/security/test_idor_probes.py` | ⬜ GATED |
| **1.7 PostgreSQL RLS Matrix** | `FORCE ROW LEVEL SECURITY` verified on all 18 tables; cross-tenant queries return 0 rows. | `pytest backend/tests/security/test_rls_isolation.py` | ⬜ GATED |

*Phase 1 Acceptance Gate*: Tenant isolation and RBAC security tests pass with 100% coverage, proving zero cross-tenant leakage.

---

### ⚪ Phase 2: Document Ingestion Pipeline (Weeks 3–4)
*Goal: Implement asynchronous multi-format document parsers, S3 storage, Celery worker orchestration, and transactional outbox publishing.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **2.1 S3 / MinIO Storage** | Object storage client securely uploads, downloads, and generates presigned URLs. | `pytest backend/tests/integration/test_storage.py` | ⬜ GATED |
| **2.2 MIME Validation** | `python-magic` validates file headers, rejecting polyglot payloads and executables. | `pytest backend/tests/security/test_magic_bytes.py` | ⬜ GATED |
| **2.3 Multi-Format Parsers** | PyMuPDF (PDF), python-docx (DOCX), email (EML), and pandas (CSV) extract clean text. | `pytest backend/tests/unit/test_parsers.py` | ⬜ GATED |
| **2.4 SHA-256 Deduplication** | Duplicate uploads in the same case are rejected via `uq_case_document_hash`. | `pytest backend/tests/integration/test_doc_dedup.py` | ⬜ GATED |
| **2.5 Transactional Outbox** | Upload commits document metadata and `outbox_events` row in a single ACID transaction. | `pytest backend/tests/integration/test_outbox_commit.py` | ⬜ GATED |
| **2.6 Outbox Relay Daemon** | Relay claims events via `FOR UPDATE SKIP LOCKED` and dispatches Celery tasks. | `pytest backend/tests/integration/test_outbox_relay.py` | ⬜ GATED |
| **2.7 Ingestion State Machine** | Jobs track `QUEUED` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` / `FAILED` $\rightarrow$ `DEAD_LETTER`. | `pytest backend/tests/integration/test_ingestion_jobs.py` | ⬜ GATED |
| **2.8 Sliding Window Chunker** | Chunks text into 500-token windows with 50-token overlap, tracking exact character offsets. | `pytest backend/tests/unit/test_chunking.py` | ⬜ GATED |

*Phase 2 Acceptance Gate*: Asynchronous upload returns `202 Accepted` in $< 1000\text{ ms}$; multi-page PDF successfully chunks and stores in PostgreSQL.

---

### ⚪ Phase 3: Knowledge Extraction & Entity Resolution (Weeks 5–6)
*Goal: Build Gemini structured extraction pipeline, verbatim offset coordinate validation, calibrated entity resolution, and pointer-based merge hierarchy.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **3.1 Gemini Extraction** | Gemini 1.5 Pro structured output (`response_schema=ExtractionResult`) extracts entities and claims. | `pytest backend/tests/integration/test_gemini_extraction.py` | ⬜ GATED |
| **3.2 Claim Target XOR Check** | Schema enforces XOR target exclusivity (`claim_type`, `chk_claim_target_exclusivity`). | `pytest backend/tests/unit/test_claim_validation.py` | ⬜ GATED |
| **3.3 Offset Alignment Trigger** | Trigger `trg_validate_claim_source_chunk_offsets` enforces chunk coordinate containment. | `pytest backend/tests/integration/test_offset_trigger.py` | ⬜ GATED |
| **3.4 Weighted Entity Resolution** | Evaluates $S = 0.35N + 0.25A + 0.25C + 0.15T$; matches aliases $> 0.90$, queues $[0.70, 0.90)$. | `pytest backend/tests/unit/test_entity_resolution.py` | ⬜ GATED |
| **3.5 Pointer Merge Hierarchy** | Merging entity $A$ into $B$ sets `entities.merged_into_id = B`; zero claims are rewritten. | `pytest backend/tests/integration/test_entity_merge.py` | ⬜ GATED |
| **3.6 Merge Cycle Prevention** | Trigger `trg_prevent_entity_merge_cycles` rejects circular merges ($A \rightarrow B \rightarrow C \rightarrow A$). | `pytest backend/tests/integration/test_merge_cycles.py` | ⬜ GATED |
| **3.7 Recursive Resolution** | `fn_get_canonical_entity_id(UUID)` traverses multi-hop merge chains to canonical root. | `pytest backend/tests/integration/test_canonical_fn.py` | ⬜ GATED |
| **3.8 Deterministic Unmerge** | Unmerging entity $A$ resets `merged_into_id = NULL`; claims retain original extracted links. | `pytest backend/tests/integration/test_entity_unmerge.py` | ⬜ GATED |
| **3.9 Cognee Synchronization** | Idempotent worker syncs claims to Cognee edges; ignores out-of-order stale versions. | `pytest backend/tests/integration/test_cognee_sync.py` | ⬜ GATED |

*Phase 3 Acceptance Gate*: Entities and claims committed to PostgreSQL and synced to Cognee; pointer-based unmerge restores pre-merge state without data loss.

---

### ⚪ Phase 4: Knowledge Graph & Hybrid Recall (Weeks 7–8)
*Goal: Implement 13-stage hybrid recall pipeline, bounded BFS graph traversal, case permission filtering, and grounded synthesis prompt.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **4.1 Query Understanding** | Extracts seed entities and relationship intent from user prompt. | `pytest backend/tests/unit/test_query_parser.py` | ⬜ GATED |
| **4.2 Dual Retrieval** | Executes simultaneous vector similarity search + bounded BFS graph traversal ($N \le 4$). | `pytest backend/tests/integration/test_dual_retrieval.py` | ⬜ GATED |
| **4.3 Permission Filtering** | Queries PostgreSQL to strip any Cognee graph nodes/edges belonging to unauthorized cases. | `pytest backend/tests/security/test_recall_permissions.py` | ⬜ GATED |
| **4.4 Evidence Ranking** | Ranks candidate evidence by extraction confidence, authority, and path length. | `pytest backend/tests/unit/test_evidence_ranking.py` | ⬜ GATED |
| **4.5 Citation Verification** | Verifies that character offsets in `claim_sources` match verbatim text in raw document bytes. | `pytest backend/tests/integration/test_citation_verification.py` | ⬜ GATED |
| **4.6 Epistemic Grounding** | LLM prompt synthesizes answers citing only verified `[Claim #ID]` tokens. | `pytest backend/tests/integration/test_grounded_synthesis.py` | ⬜ GATED |
| **4.7 Unanswerable Fallback** | Missing evidence triggers exact fallback: *"The available evidence does not establish a connection."* | `pytest backend/tests/integration/test_unanswerable_fallback.py` | ⬜ GATED |
| **4.8 Recall Latency SLA** | Median retrieval latency $< 500\text{ ms}$; end-to-end answer latency $< 2.5\text{ s}$ (p50). | `pytest backend/tests/benchmarks/test_retrieval_latency.py` | ⬜ GATED |

*Phase 4 Acceptance Gate*: Multi-hop questions return verified graph path and page-level citations; unanswerable queries return fallback message.

---

### ⚪ Phase 5: Contradiction Management & Claim Lifecycle (Week 9)
*Goal: Implement decoupled claim state machine, dispute challenges, review decisions, immutable version snapshots, and audited historical recall.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **5.1 Dispute Challenge API** | `POST /api/v1/claims/{id}/challenge` updates status to `DISPUTED` and logs counter-evidence. | `pytest backend/tests/integration/test_claim_challenge.py` | ⬜ GATED |
| **5.2 Review Decision API** | `POST /api/v1/claims/{id}/review` updates `review_outcome` (`UPHELD`, `REJECTED`, `INCONCLUSIVE`). | `pytest backend/tests/integration/test_claim_review.py` | ⬜ GATED |
| **5.3 Immutable Snapshots** | Every mutation creates an immutable row in `claim_versions` recording actor ID and reason. | `pytest backend/tests/integration/test_claim_versions.py` | ⬜ GATED |
| **5.4 Transition Audit Ledger** | Every transition logs `claim_events` with prior status, new status, and counter citations. | `pytest backend/tests/integration/test_claim_events.py` | ⬜ GATED |
| **5.5 Disputed Claim Warnings** | Recall pipeline injects mandatory amber dispute warnings and counter-citations for disputed claims. | `pytest backend/tests/integration/test_dispute_recall.py` | ⬜ GATED |
| **5.6 Retracted Claim Exclusion** | Retracted claims are excluded from default graph traversal and RAG synthesis. | `pytest backend/tests/integration/test_retracted_exclusion.py` | ⬜ GATED |
| **5.7 Claim Reinstatement** | `POST /api/v1/claims/{id}/reinstate` transitions `RETRACTED` back to `ACTIVE` with audit entry. | `pytest backend/tests/integration/test_claim_reinstatement.py` | ⬜ GATED |

*Phase 5 Acceptance Gate*: Before-and-after contradiction test verifies disputed claim triggers dispute warnings and counter-citations.

---

### ⚪ Phase 6: Frontend Investigation Workspace (Weeks 10–11)
*Goal: Build Next.js 15 App Router interface, interactive 3-panel workspace, Force Graph 2D with dispute styling, and immutable report generation.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **6.1 Next.js 15 App Shell** | App Router boots cleanly with authentication context, TanStack Query v5, and Tailwind CSS. | `npm run build && npm run test` (in `frontend/`) | ⬜ GATED |
| **6.2 3-Panel Workspace** | Left Panel (Case tree/docs), Center Panel (Graph/reader), Right Panel (Evidence/claims). | `npx playwright test tests/e2e/workspace_layout.spec.ts` | ⬜ GATED |
| **6.3 Graph Visualizer** | `react-force-graph-2d` renders entities as nodes, claims as directed edges. | `npx playwright test tests/e2e/graph_render.spec.ts` | ⬜ GATED |
| **6.4 Dispute Styling** | Disputed claims render as amber dashed lines; retracted claims visually filtered out. | `npx playwright test tests/e2e/dispute_styling.spec.ts` | ⬜ GATED |
| **6.5 Claim Challenge Modal** | Investigators can challenge a claim from the UI, uploading counter-evidence attachments. | `npx playwright test tests/e2e/claim_challenge_ui.spec.ts` | ⬜ GATED |
| **6.6 Report Generation API** | `POST /api/v1/cases/{id}/reports` freezes evidence snapshot into PDF and machine-readable JSON. | `pytest backend/tests/integration/test_report_generation.py` | ⬜ GATED |

*Phase 6 Acceptance Gate*: Playwright E2E browser tests pass complete end-to-end investigation workflow from login to report export.

---

### ⚪ Phase 7: Optimization, Benchmark & Production Readiness (Week 12)
*Goal: Index tuning, Redis caching, 200-question ground-truth evaluation execution, latency SLA validation, and production CI/CD.*

| Gate Item | Verification Criterion / Target | Verification Command | Status |
| :--- | :--- | :--- | :---: |
| **7.1 Index Optimization** | EXPLAIN (ANALYZE, BUFFERS) proves index scans for all hot paths ($< 10\text{ ms}$ index lookups). | `pytest backend/tests/benchmarks/test_query_plans.py` | ⬜ GATED |
| **7.2 Redis Subgraph Cache** | Frequently queried canonical entity subgraphs cached in Redis with TTL invalidation. | `pytest backend/tests/integration/test_redis_cache.py` | ⬜ GATED |
| **7.3 200-Question Benchmark** | Benchmark harness runs all 200 questions across Dev (60), Val (40), and Held-Out Test (100). | `python backend/eval/run_benchmark.py --split test` | ⬜ GATED |
| **7.4 Faithfulness Score** | Held-Out Test set achieves $\ge 98\%$ Faithfulness score. | `python backend/eval/score_eval.py --metric faithfulness` | ⬜ GATED |
| **7.5 Unsupported Rate** | Held-Out Test set achieves $0.0\%$ Unsupported Answer Rate. | `python backend/eval/score_eval.py --metric unsupported_rate` | ⬜ GATED |
| **7.6 Latency SLA Verification** | Median retrieval latency $< 500\text{ ms}$, p95 query latency $< 5.0\text{ s}$ under load. | `locust -f backend/tests/load/locustfile.py --headless -u 10 -t 5m` | ⬜ GATED |
| **7.7 Automated CI/CD** | GitHub Actions pipeline runs linting (`ruff`, `mypy`), pytest, and security scanning on PR. | Push to branch triggers GitHub Actions workflow | ⬜ GATED |

*Phase 7 Acceptance Gate*: Complete 200-question benchmark suite executed; latency SLAs met; automated CI/CD pipeline green.

---

## 3. Database Schema & Migration Readiness Checklist

Verification checklist for all 18 PostgreSQL tables before running migrations:

- [ ] **Table 1: `organizations`**: Primary key `id UUID`, unique `name`, delete policy `RESTRICT`.
- [ ] **Table 2: `users`**: Primary key `id UUID`, unique `email`, `password_hash`, delete policy `RESTRICT`.
- [ ] **Table 3: `memberships`**: Composite PK `(organization_id, user_id)`, role `org_role`.
- [ ] **Table 4: `cases`**: Composite candidate key `(organization_id, id)`, `case_number`, status `case_status`.
- [ ] **Table 5: `case_members`**: Composite PK `(case_id, user_id)`, composite FK `(organization_id, case_id)`.
- [ ] **Table 6: `documents`**: Composite candidate key `(case_id, id)`, unique `(case_id, content_hash)`.
- [ ] **Table 7: `document_chunks`**: Composite candidate key `(document_id, id)`, unique `(document_id, chunk_index)`.
- [ ] **Table 8: `ingestion_jobs`**: Job status `ingestion_status`, retry counter, exponential backoff timestamp.
- [ ] **Table 9: `entities`**: Composite candidate key `(organization_id, id)`, unique `(organization_id, canonical_name, entity_type)`.
- [ ] **Table 10: `entity_aliases`**: Unique `(entity_id, alias)`, trigram index on `alias`.
- [ ] **Table 11: `entity_merge_events`**: Audit ledger with `source_entity_id`, `target_entity_id`, `merged_by`, `unmerged_at`.
- [ ] **Table 12: `case_entities`**: Composite PK `(case_id, entity_id)`.
- [ ] **Table 13: `claims`**: Composite candidate key `(case_id, id)`, `claim_type`, `qualifiers JSONB`, `chk_claim_target_exclusivity`.
- [ ] **Table 14: `claim_sources`**: Composite FKs `(case_id, claim_id)`, `(case_id, document_id)`, `(document_id, chunk_id)`, offsets.
- [ ] **Table 15: `claim_versions`**: Append-only snapshot ledger with `(claim_id, version)` unique key.
- [ ] **Table 16: `claim_events`**: Transition event ledger with `prior_status`, `new_status`, `reason`.
- [ ] **Table 17: `outbox_events`**: Status `outbox_status`, `aggregate_id`, `aggregate_version`, lease columns.
- [ ] **Table 18: `audit_logs` & `reports`**: Compliance audit trail and frozen evidence dossiers.
- [ ] **Database Trigger**: `trg_prevent_entity_merge_cycles` registered on `entities`.
- [ ] **Database Trigger**: `trg_validate_claim_source_chunk_offsets` registered on `claim_sources`.
- [ ] **Database Function**: `fn_get_canonical_entity_id(UUID)` registered and tested.
- [ ] **Database View**: `vw_canonical_entities` registered and tested.
- [ ] **RLS Matrix**: `FORCE ROW LEVEL SECURITY` executed on all 18 tables.

---

## 4. Module Implementation Sequence Checklist (MOD-01 through MOD-10)

- [ ] **MOD-01: User Authentication & Organization Management**:
  - Prerequisite: Phase 0 Schema.
  - Deliverable: JWT tokens, Argon2id, RBAC dependency, tenant context injection.
- [ ] **MOD-02: Case Management**:
  - Prerequisite: MOD-01.
  - Deliverable: Case workspaces, investigator assignments, non-disclosing 404s.
- [ ] **MOD-03: Document Ingestion Pipeline**:
  - Prerequisite: MOD-02.
  - Deliverable: PyMuPDF, python-docx, Celery tasks, S3 storage, Outbox relay.
- [ ] **MOD-04: Entity and Relationship Extraction**:
  - Prerequisite: MOD-03.
  - Deliverable: Gemini structured output, coordinate offset calculation, Pydantic validation.
- [ ] **MOD-05: Entity Resolution**:
  - Prerequisite: MOD-04.
  - Deliverable: Weighted formula $S$, alias index, review queue, pointer-based merges.
- [ ] **MOD-06: Knowledge Graph & Cross-Case Intelligence**:
  - Prerequisite: MOD-05.
  - Deliverable: Cognee sync, BFS traversal, cross-case overlap discovery.
- [ ] **MOD-07: Intelligent Recall & Grounded RAG**:
  - Prerequisite: MOD-06.
  - Deliverable: 13-stage pipeline, permission filtering, citation verification, prompt synthesis.
- [ ] **MOD-08: Contradiction Detection & Intelligent Forgetting**:
  - Prerequisite: MOD-07.
  - Deliverable: Claim dispute API, review outcome evaluation, dispute styling warnings.
- [ ] **MOD-09: Search, Analytics & Investigation Workspace**:
  - Prerequisite: MOD-08.
  - Deliverable: 3-panel Next.js UI, force-directed graph view, dispute styling.
- [ ] **MOD-10: Reports and Export**:
  - Prerequisite: MOD-09.
  - Deliverable: PDF / JSON / CSV dossier export with immutable evidence snapshots.

---

## 5. Summary Sign-Off

| Role | Name / Title | Determination | Signature Date |
| :--- | :--- | :---: | :---: |
| **Principal Backend Architect** | Lead Systems Architect | **APPROVED FOR PHASE 0** | 2026-11-18 |
| **PostgreSQL Database Architect** | Principal Database Engineer | **APPROVED FOR PHASE 0** | 2026-11-18 |
| **Application Security Engineer** | Lead SecOps Engineer | **APPROVED FOR PHASE 0** | 2026-11-18 |
| **Distributed Systems Engineer** | Staff Infrastructure Engineer | **APPROVED FOR PHASE 0** | 2026-11-18 |

---

## 6. Related Documents
- [Final Documentation Audit Report](FINAL_DOCUMENTATION_AUDIT.md)
- [Master Documentation Index](../README.md)
- [System Architecture](../architecture.md)
- [Development Roadmap](../roadmap.md)
- [Definition of Done](../definition-of-done.md)
