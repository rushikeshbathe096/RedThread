# RedThread Definition of Done (DoD)

> **Document Status**: `DESIGN`  
> **Quality Standard**: No feature or phase may be marked `IMPLEMENTED` or `VERIFIED` without meeting the criteria outlined in this document.

---

## 1. Universal Feature Definition of Done

Every feature implemented in RedThread must satisfy the following checklist before merging into the main branch:

### 1.1 Architecture & Code Quality
- [ ] Code strictly adheres to the modular monolith boundaries (`api/`, `services/`, `repositories/`, `models/`, `workers/`).
- [ ] 100% type annotations with `mypy` passing under strict mode.
- [ ] No hardcoded secrets, database URLs, or API keys.
- [ ] Pure business logic is decoupled from HTTP transport and ORM database sessions.

### 1.2 Data Integrity & Security
- [ ] Database schema changes are managed via versioned Alembic migrations.
- [ ] Every query touching tenant data enforces both `organization_id` and authorized `case_id`.
- [ ] All mutations write to immutable `audit_logs` or `claim_events`.
- [ ] Uploaded files are validated via magic bytes and size constraints.

### 1.3 Testing & Verification
- [ ] Unit tests cover happy path, boundary conditions, and invalid inputs.
- [ ] Integration tests verify database persistence with transaction rollbacks.
- [ ] Security tests explicitly verify rejection of cross-tenant and unauthorized role actions.
- [ ] CI pipeline passes with zero warnings or test failures.

### 1.4 Documentation Synchronization
- [ ] API endpoints, request schemas, and responses match `docs/api-specification.md`.
- [ ] Database models and migrations match `docs/database-design.md`.
- [ ] Module status in `docs/implementation-status.md` is updated accurately.

---

## 2. Phase-by-Phase Acceptance Gates

### Phase 0: Repository Foundation & Test Baselines
- [ ] `infrastructure/docker-compose.yml` launches PostgreSQL 16, Redis 7, MinIO, API, and Worker cleanly.
- [ ] Environment variables and configuration loaded securely via Pydantic `BaseSettings`.
- [ ] Alembic initialized; initial migration builds the foundational schema without errors.
- [ ] Baseline test runner executes with `pytest` passing.

### Phase 1: Authentication & Multi-Tenancy
- [ ] User registration, login, refresh token rotation, and logout pass automated integration tests.
- [ ] Passwords hashed with Argon2id using OWASP-recommended parameters.
- [ ] Multi-tenancy security tests confirm that User A cannot read or mutate Case B in a different organization (returning non-disclosing 404s).
- [ ] RBAC permissions correctly restrict Viewer, Reviewer, Investigator, and Admin roles.

### Phase 2: Document Ingestion Pipeline
- [ ] Uploading a document via `POST /api/v1/cases/{id}/documents` returns `202 Accepted` in $< 1000\text{ ms}$.
- [ ] Celery worker asynchronously downloads file from S3, executes parsing, and tracks progress.
- [ ] Duplicate upload detection (SHA-256) rejects or references existing document without re-processing.
- [ ] Ingestion failure tests confirm that transient errors trigger exponential backoff and dead-letter handling.
- [ ] Transactional outbox guarantees event publishing from PostgreSQL to Redis.

### Phase 3: Knowledge Extraction & Entity Resolution
- [ ] Gemini extraction pipeline populates structured Pydantic models with page and offset coordinates.
- [ ] Weighted entity resolution ($S = 0.35N + 0.25A + 0.25C + 0.15T$) evaluates incoming entities against existing clusters.
- [ ] High-confidence candidates ($S \ge 0.90$) auto-link as aliases; ambiguous candidates ($0.70 \le S < 0.90$) route to the manual review queue.
- [ ] Reversible merge and unmerge operations restore pre-merge relationship state without data corruption.

### Phase 4: Knowledge Graph & Hybrid Recall
- [ ] Dual retrieval executes BFS/Dijkstra graph traversal in Cognee and vector passage similarity search.
- [ ] Authorization filter strips any graph nodes or edges outside the user's active case scope.
- [ ] Grounded answer generation strictly cites `[Claim #ID]`; unsupported queries output `"Insufficient evidence"`.
- [ ] Initial evaluation benchmark runs and generates reproducible accuracy metrics.

### Phase 5: Contradiction Management & Claim Lifecycle
- [ ] Claim state transitions (`ACTIVE`, `DISPUTED`, `RETRACTED`) adhere to the state machine.
- [ ] Every challenge or review creates an immutable record in `claim_events`.
- [ ] Disputed claims in recall answers are explicitly highlighted with dispute warnings and counter-citations.
- [ ] Retracted claims are excluded from standard recall answers but remain accessible in audit history.

### Phase 6: Frontend Investigation Workspace
- [ ] 3-panel workspace renders case navigation (left), force-directed knowledge graph (center), and evidence details (right).
- [ ] Graph dynamically updates with dispute styling (amber dashed lines for disputed claims).
- [ ] Investigator can upload documents, query AI recall, challenge claims, and review disputes in the UI.
- [ ] Export engine generates frozen PDF, JSON, and CSV investigation reports.

### Phase 7: Optimization & Production Readiness
- [ ] p95 API latency $< 300\text{ ms}$; end-to-end query latency $< 2.5\text{ seconds}$.
- [ ] Ingestion throughput achieves $\ge 5\text{ documents/minute}$.
- [ ] Full 200-question benchmark executed and results documented in `docs/benchmarks/`.
- [ ] All documentation verified with zero broken links or contradictions.

---

## 3. Related Documents
- [Implementation Status](implementation-status.md)
- [Testing Strategy](testing-strategy.md)
- [Development Roadmap](roadmap.md)
